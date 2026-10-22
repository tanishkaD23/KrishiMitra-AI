"""Reproducible Training & Evaluation Pipeline for Official UP District APY Dataset.

Evaluates against simple heuristic baselines (Global Mean, District Historical Mean,
and Previous-Year Persistence) using a temporal out-of-time split (2012-2020 train, 2021-2023 test).
Strictly prevents data leakage by excluding total production.
"""

import json
from pathlib import Path
from typing import Dict, Any
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

from config.settings import MODELS_DIR, PROCESSED_DATA_DIR
from src.data_pipeline.up_apy_processor import process_up_apy_raw_data


def train_and_evaluate_up_apy() -> Dict[str, Any]:
    """Trains and benchmarks ML pipelines on official UP APY time-series."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tidy_path = PROCESSED_DATA_DIR / "up_district_apy_tidy.csv"

    if not tidy_path.exists():
        df = process_up_apy_raw_data()
    else:
        df = pd.read_csv(tidy_path)

    # Clean initial NaN lag rows (2012 and 2013)
    df_clean = df.dropna().reset_index(drop=True)

    # Temporal Out-of-Time Split
    train_mask = df_clean["start_year"] <= 2020
    test_mask = df_clean["start_year"] >= 2021

    train_df = df_clean[train_mask]
    test_df = df_clean[test_mask]

    num_features = [
        "area_hectares",
        "yield_lag_1",
        "yield_lag_2",
        "yield_rolling_3yr",
        "area_pct_change",
    ]
    cat_features = ["district"]
    target_col = "yield_tonne_per_hectare"

    feature_cols = num_features + cat_features
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    evaluation = {}

    # --- 1. Evaluate Simple Baselines ---
    # Baseline 1: Global Mean
    global_mean = float(y_train.mean())
    b1_preds = np.full(shape=(len(y_test),), fill_value=global_mean)
    evaluation["Baseline_1_Global_Mean"] = {
        "description": f"Predicts constant training mean ({global_mean:.2f} t/ha)",
        "test_mae_tonne_per_ha": round(float(mean_absolute_error(y_test, b1_preds)), 3),
        "test_rmse_tonne_per_ha": round(float(root_mean_squared_error(y_test, b1_preds)), 3),
        "test_r2": round(float(r2_score(y_test, b1_preds)), 4),
        "equiv_mae_q_acre": round(float(mean_absolute_error(y_test, b1_preds)) * 4.047, 2),
    }

    # Baseline 2: District Historical Mean
    dist_means = train_df.groupby("district")[target_col].mean().to_dict()
    b2_preds = test_df["district"].map(dist_means).values
    evaluation["Baseline_2_District_Historical_Mean"] = {
        "description": "Predicts each district's own 8-year historical average yield",
        "test_mae_tonne_per_ha": round(float(mean_absolute_error(y_test, b2_preds)), 3),
        "test_rmse_tonne_per_ha": round(float(root_mean_squared_error(y_test, b2_preds)), 3),
        "test_r2": round(float(r2_score(y_test, b2_preds)), 4),
        "equiv_mae_q_acre": round(float(mean_absolute_error(y_test, b2_preds)) * 4.047, 2),
    }

    # Baseline 3: Naive Lag-1 Persistence
    b3_preds = test_df["yield_lag_1"].values
    evaluation["Baseline_3_Naive_Persistence"] = {
        "description": "Predicts last year's observed yield directly (Yield_t = Yield_t-1)",
        "test_mae_tonne_per_ha": round(float(mean_absolute_error(y_test, b3_preds)), 3),
        "test_rmse_tonne_per_ha": round(float(root_mean_squared_error(y_test, b3_preds)), 3),
        "test_r2": round(float(r2_score(y_test, b3_preds)), 4),
        "equiv_mae_q_acre": round(float(mean_absolute_error(y_test, b3_preds)) * 4.047, 2),
    }

    # --- 2. Evaluate ML Pipelines ---
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_features),
        ]
    )

    models = {
        "Linear_Ridge": Ridge(alpha=1.0),
        "XGBoost": XGBRegressor(
            n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42
        ),
    }

    best_pipeline = None
    best_name = None
    best_rmse = float("inf")

    for name, reg in models.items():
        pipe = Pipeline([("preprocessor", preprocessor), ("regressor", reg)])
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)

        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(root_mean_squared_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))

        evaluation[name] = {
            "test_mae_tonne_per_ha": round(mae, 3),
            "test_rmse_tonne_per_ha": round(rmse, 3),
            "test_r2": round(r2, 4),
            "equiv_mae_q_acre": round(mae * 4.047, 2),
        }

        print(f"[{name}] Test MAE: {mae:.3f} t/ha | RMSE: {rmse:.3f} t/ha | R²: {r2:.4f}")

        if rmse < best_rmse:
            best_rmse = rmse
            best_name = name
            best_pipeline = pipe

    # Save artifact
    model_path = MODELS_DIR / "best_up_district_apy_model.joblib"
    joblib.dump(best_pipeline, model_path)

    report = {
        "dataset": "Official Uttar Pradesh District APY (2012-13 to 2022-23)",
        "total_records": len(df_clean),
        "train_records": len(X_train),
        "test_records": len(X_test),
        "target": target_col,
        "target_unit": "Tonne / Hectare",
        "benchmarks": evaluation,
        "selected_model": best_name,
        "strict_scope_limitations": [
            "Dataset operates strictly at the DISTRICT LEVEL across 75 districts of UP.",
            "Never claim certified plot-level accuracy from district aggregates.",
            "Production (Tonnes) was strictly excluded from features to prevent deterministic division leakage (Yield = Production / Area).",
            "Out-of-time evaluation split (2012-2020 train, 2021-2023 test) prevents temporal leakage.",
        ],
    }

    report_path = MODELS_DIR / "up_district_apy_evaluation.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nTop model saved to {model_path}")
    print(f"Audit & evaluation report saved to {report_path}")
    return report


if __name__ == "__main__":
    train_and_evaluate_up_apy()
