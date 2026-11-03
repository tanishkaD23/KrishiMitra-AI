"""Unified Multi-State Crop, Soil, and Weather Dataset Processor & Trainer for KrishiMitra AI.

Integrates the three newly uploaded datasets:
1. `all state crops.zip` (6 official APY files: Bihar, Haryana, MP, Punjab, Rajasthan, UP -> 19,863 records across 243+ districts and 26 Rabi crops)
2. `soil info 6 states.csv` (500 district-level Soil Health Card & SoilGrids records across all 6 states)
3. `weather_rainfall_datasets.csv` (10,648 daily/seasonal temperature, humidity, solar radiation & rainfall records across all 6 states)

Outputs:
- `data/processed/multi_state_rabi_data.csv` (Consolidated 19,863-row multi-state & multi-crop dataset)
- `models/multi_state_yield_model.pkl` & `models/model_feature_columns.pkl`
"""

import io
import os
import re
import zipfile
from typing import Dict, Tuple, Optional
import joblib
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from config.settings import BASE_DIR, PROCESSED_DATA_DIR, MODELS_DIR


def clean_name(val: object) -> str:
    if not isinstance(val, str):
        return ""
    cleaned = re.sub(r"^\d+\.\s*", "", val).strip().title()
    alias_map = {
        "Allahabad": "Prayagraj",
        "Hoshangabad": "Narmadapuram",
        "Ganganagar": "Sri Ganganagar",
        "Firozepur": "Ferozepur",
    }
    return cleaned


def normalize_crop_name(raw_crop: str) -> str:
    c = str(raw_crop).strip()
    if c.lower() in {"rapeseed &mustard", "rapeseed & mustard", "mustard"}:
        return "Mustard"
    return c


def parse_crop_archive(zip_path: Optional[str] = None) -> pd.DataFrame:
    """Parses all 6 state HTML-based `.xls` files inside `all state crops.zip`."""
    if zip_path is None:
        zip_path = str(BASE_DIR / "all state crops.zip")
    if not os.path.exists(zip_path):
        return pd.DataFrame()

    records = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for fname in z.namelist():
            html_content = z.open(fname).read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html_content, "html.parser")
            trs = soup.find_all("tr")
            if len(trs) < 4:
                continue

            r0 = [c.get_text(strip=True) for c in trs[0].find_all(["th", "td"])]
            crops = [c for c in r0[3:] if c]

            cur_state = ""
            cur_dist = ""
            for tr in trs[3:]:
                cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
                if not cells:
                    continue

                if len(cells) == 3 + len(crops) * 3:
                    cur_state = clean_name(cells[0])
                    cur_dist = clean_name(cells[1])
                    yr_str = cells[2]
                    data_cells = cells[3:]
                elif len(cells) == 2 + len(crops) * 3:
                    cur_dist = clean_name(cells[0])
                    yr_str = cells[1]
                    data_cells = cells[2:]
                elif len(cells) == 1 + len(crops) * 3:
                    yr_str = cells[0]
                    data_cells = cells[1:]
                else:
                    continue

                if "Total" in cur_dist or "Total" in yr_str or not cur_state:
                    continue

                try:
                    year = int(str(yr_str).split("-")[0].strip())
                except ValueError:
                    continue

                for idx, raw_crop in enumerate(crops):
                    base = idx * 3
                    if base + 2 >= len(data_cells):
                        continue
                    a_s, p_s, y_s = data_cells[base], data_cells[base + 1], data_cells[base + 2]
                    try:
                        area = float(a_s.replace(",", "")) if a_s else 0.0
                        prod = float(p_s.replace(",", "")) if p_s else 0.0
                        yield_t_ha = float(y_s.replace(",", "")) if y_s else 0.0
                    except ValueError:
                        continue

                    if area > 0 and (yield_t_ha > 0 or prod > 0):
                        if yield_t_ha <= 0 and prod > 0:
                            yield_t_ha = prod / area

                        yield_q_acre = round(yield_t_ha * 4.04686, 2)
                        records.append({
                            "state": cur_state,
                            "district": cur_dist,
                            "year": year,
                            "year_label": f"{year}-{year + 1}",
                            "crop": normalize_crop_name(raw_crop),
                            "raw_crop": raw_crop,
                            "season": "Rabi",
                            "area_ha": round(area, 2),
                            "production_tonnes": round(prod, 2),
                            "yield_tonne_ha": round(yield_t_ha, 3),
                            "yield_q_acre": yield_q_acre,
                        })

    df_crops = pd.DataFrame(records)
    print(f"Extracted {len(df_crops)} valid crop records across {df_crops['state'].nunique()} states and {df_crops['district'].nunique()} districts.")
    return df_crops


def load_soil_and_weather_Lookup(
    soil_csv: Optional[str] = None,
    weather_csv: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads and cleans `soil info 6 states.csv` and `weather_rainfall_datasets.csv`."""
    if soil_csv is None:
        soil_csv = str(BASE_DIR / "soil info 6 states.csv")
    if weather_csv is None:
        weather_csv = str(BASE_DIR / "weather_rainfall_datasets.csv")

    # 1. Parse Soil CSV (handling outer quote-wrapped lines cleanly)
    soil_summary = pd.DataFrame()
    if os.path.exists(soil_csv):
        with open(soil_csv, "r", encoding="utf-8") as f:
            raw_lines = [l.strip() for l in f if l.strip()]
        cleaned_lines = []
        for l in raw_lines:
            if l.startswith('"') and l.endswith('"'):
                l = l[1:-1].replace('""', '"')
            cleaned_lines.append(l)
        df_soil = pd.read_csv(io.StringIO("\n".join(cleaned_lines)))
        df_soil["state"] = df_soil["state"].apply(clean_name)
        df_soil["district"] = df_soil["district"].apply(clean_name)

        num_cols = [
            "nitrogen_medium_pct",
            "phosphorus_medium_pct",
            "potassium_medium_pct",
            "organic_carbon_medium_pct",
            "ph_neutral_pct",
            "nitrogen_kg_per_hectare",
            "phosphorous_kg_per_hectare",
            "potassium_kg_per_hectare",
            "ph",
            "organic_carbon_percentage",
        ]
        for c in num_cols:
            if c in df_soil.columns:
                df_soil[c] = pd.to_numeric(df_soil[c], errors="coerce")

        agg_map = {c: "mean" for c in num_cols if c in df_soil.columns}
        soil_summary = df_soil.groupby(["state", "district"], as_index=False).agg(agg_map)

    # 2. Parse Weather & Rainfall CSV
    weather_summary = pd.DataFrame()
    if os.path.exists(weather_csv):
        df_weather = pd.read_csv(weather_csv)
        df_weather["state"] = df_weather["State"].apply(clean_name)
        df_weather["district"] = df_weather["District"].apply(clean_name)
        df_weather["year"] = pd.to_numeric(df_weather["Year"], errors="coerce").fillna(2020).astype(int)

        weather_summary = (
            df_weather.groupby(["state", "district", "year"], as_index=False)
            .agg({
                "Current_Temp_C": "mean",
                "Relative_Humidity_pct": "mean",
                "Rainfall_Current_mm": "sum",
                "Rainfall_Rolling_Sum_7d_mm": "mean",
                "Solar_Radiation_MJ_m2": "mean",
            })
            .rename(columns={
                "Current_Temp_C": "avg_temp_c",
                "Relative_Humidity_pct": "avg_humidity_pct",
                "Rainfall_Current_mm": "seasonal_rainfall_mm",
                "Rainfall_Rolling_Sum_7d_mm": "rolling_7d_rain_mm",
                "Solar_Radiation_MJ_m2": "solar_rad_mj_m2",
            })
        )

    return soil_summary, weather_summary


def merge_soil_and_weather(
    df_crops: pd.DataFrame,
    soil_csv: Optional[str] = None,
    weather_csv: Optional[str] = None,
) -> pd.DataFrame:
    """Merges empirical crop records with district soil profiles and seasonal weather telemetry."""
    soil_summary, weather_summary = load_soil_and_weather_Lookup(soil_csv, weather_csv)

    merged = df_crops.copy()
    if not soil_summary.empty:
        merged = pd.merge(merged, soil_summary, on=["state", "district"], how="left")
    if not weather_summary.empty:
        merged = pd.merge(merged, weather_summary, on=["state", "district", "year"], how="left")

    # Fill missing district/year joins using state-level medians then global medians
    numeric_cols = merged.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if merged[col].isna().any():
            merged[col] = merged.groupby("state")[col].transform(lambda s: s.fillna(s.median()))
            merged[col] = merged[col].fillna(merged[col].median())

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / "multi_state_rabi_data.csv"
    merged.to_csv(out_path, index=False)
    print(f"Consolidated multi-state dataset saved to {out_path} ({len(merged)} rows).")
    return merged


def train_and_export_model(df: pd.DataFrame) -> Dict[str, float]:
    """Trains a compact multi-state, multi-crop Random Forest model and exports artifacts."""
    feature_cols = [
        "area_ha",
        "nitrogen_medium_pct",
        "phosphorus_medium_pct",
        "potassium_medium_pct",
        "organic_carbon_medium_pct",
        "ph_neutral_pct",
        "avg_temp_c",
        "avg_humidity_pct",
        "seasonal_rainfall_mm",
        "solar_rad_mj_m2",
    ]
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 50.0

    categoricals = pd.get_dummies(df[["state", "district", "crop"]], drop_first=True)
    X = pd.concat([df[feature_cols], categoricals], axis=1)
    y = df["yield_q_acre"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=60,
        max_depth=14,
        min_samples_leaf=2,
        n_jobs=1,
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    r2 = float(r2_score(y_test, preds))
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))

    print(f"--- Multi-State Empirical Crop Model Evaluation ---")
    print(f"Samples: {len(df)} | R² Score: {r2:.4f} | MAE: {mae:.4f} | RMSE: {rmse:.4f} Q/Acre")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS_DIR / "multi_state_yield_model.pkl", compress=3)
    joblib.dump(list(X.columns), MODELS_DIR / "model_feature_columns.pkl", compress=3)
    return {"r2": r2, "mae": mae, "rmse": rmse, "samples": len(df)}


if __name__ == "__main__":
    crops_df = parse_crop_archive()
    full_df = merge_soil_and_weather(crops_df)
    train_and_export_model(full_df)
