"""Processor for official Uttar Pradesh District APY (Area-Production-Yield) time-series data."""

from pathlib import Path
import pandas as pd
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR


def process_up_apy_raw_data() -> pd.DataFrame:
    """Parses multi-header UP district APY time series (2012-13 to 2022-23)

    into a canonical long/tidy format with engineered non-leaking features.
    """
    raw_path = RAW_DATA_DIR / "up_district_apy_raw.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {raw_path}")

    with open(raw_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    header_years = lines[0].split(",")
    header_metrics = lines[1].split(",")

    year_blocks = []
    current_year = None
    for i, y in enumerate(header_years[3:], start=3):
        if y:
            current_year = y.replace(" ", "")
        metric = header_metrics[i].strip()
        year_blocks.append((i, current_year, metric))

    rows = []
    for line in lines[2:]:
        parts = [p.strip() for p in line.split(",")]
        state = parts[1] if parts[1] else "Uttar Pradesh"
        district = parts[2]

        for idx, year, metric in year_blocks:
            if idx < len(parts) and parts[idx]:
                try:
                    val = float(parts[idx])
                    rows.append(
                        {
                            "state": state,
                            "district": district,
                            "year": year,
                            "metric": metric,
                            "value": val,
                        }
                    )
                except ValueError:
                    continue

    df_tidy = pd.DataFrame(rows)
    df_wide = df_tidy.pivot_table(
        index=["state", "district", "year"], columns="metric", values="value"
    ).reset_index()
    df_wide.columns.name = None

    # Standardize column naming
    df_wide.rename(
        columns={
            "Area (Hectare)": "area_hectares",
            "Production (Tonnes)": "production_tonnes",
            "Yield (Tonne/Hectare)": "yield_tonne_per_hectare",
        },
        inplace=True,
    )

    # Convert yield to Quintals per Acre as smallholder reference
    # 1 Tonne/Hectare = 10 Quintals / 2.471 Acres ≈ 4.04686 Quintals/Acre
    df_wide["yield_quintals_per_acre"] = (
        df_wide["yield_tonne_per_hectare"] * 4.04686
    ).round(2)

    # Chronological sort and feature engineering (lagged variables)
    df_wide["start_year"] = df_wide["year"].apply(lambda y: int(y.split("-")[0]))
    df_wide.sort_values(by=["district", "start_year"], inplace=True)
    df_wide.reset_index(drop=True, inplace=True)

    # Engineer non-leaking historical lag features per district
    # NOTE: Never use production_tonnes as input to predict yield (deterministic leakage)
    df_wide["yield_lag_1"] = df_wide.groupby("district")["yield_tonne_per_hectare"].shift(1)
    df_wide["yield_lag_2"] = df_wide.groupby("district")["yield_tonne_per_hectare"].shift(2)
    df_wide["yield_rolling_3yr"] = (
        df_wide.groupby("district")["yield_tonne_per_hectare"]
        .transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
        .round(3)
    )
    df_wide["area_pct_change"] = (
        df_wide.groupby("district")["area_hectares"].pct_change().round(4)
    )

    output_path = PROCESSED_DATA_DIR / "up_district_apy_tidy.csv"
    df_wide.to_csv(output_path, index=False)
    print(f"Processed tidy APY dataset saved to {output_path} with shape: {df_wide.shape}")
    return df_wide


if __name__ == "__main__":
    process_up_apy_raw_data()
