"""Reproducible Preprocessing & Model Evaluation Pipeline for KrishiMitra AI.

Benchmarks machine learning models against simple heuristic baselines
(Global Mean and Crop-Stratified Mean) with MAE, RMSE, and 5-fold CV.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from config.settings import MODELS_DIR
from src.data_pipeline.data_loader import load_or_generate_dataset
from src.yield_model.feature_engineering import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
    get_preprocessor,
)


class GlobalMeanRegressor(BaseEstimator, RegressorMixin):
    """Heuristic Baseline 1: Predicts the overall mean target value of training data."""

    def __init__(self):
        self.mean_ = None

    def fit(self, X, y):
        self.mean_ = float(np.mean(y))
        return self

    def predict(self, X):
        return np.full(shape=(len(X),), fill_value=self.mean_)


class CropStratifiedMeanRegressor(BaseEstimator, RegressorMixin):
    """Heuristic Baseline 2: Predicts crop-specific historical mean yield."""

    def __init__(self, crop_col: str = "crop"):
        self.crop_col = crop_col
        self.crop_means_ = {}
        self.global_mean_ = None

    def fit(self, X, y):
        df = X.copy()
        df["target"] = y
        self.crop_means_ = df.groupby(self.crop_col)["target"].mean().to_dict()
        self.global_mean_ = float(np.mean(y))
        return self

    def predict(self, X):
        crops = X[self.crop_col]
        return np.array([self.crop_means_.get(c, self.global_mean_) for c in crops])


def run_reproducible_pipeline(
    test_size: float = 0.2, random_state: int = 42
) -> Dict[str, Any]:
    """Executes a fully reproducible pipeline:

    1. Loads audited Western UP Rabi dataset.
    2. Performs stratified train/test split.
    3. Evaluates simple heuristic baselines (Global Mean, Crop Mean).
    4. Evaluates Ridge, Random Forest, and XGBoost with preprocessor.
    5. Saves best model and exports complete benchmark report.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_or_generate_dataset()

    feature_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    X = df[feature_cols]
    y = df[TARGET_COLUMN]

    # Stratify by crop to preserve 63% Wheat / 37% Mustard ratio
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=df["crop"]
    )

    evaluation_results = {}

    # --- 1. Evaluate Simple Heuristic Baselines ---
    # Baseline 1: Global Mean
    b1 = GlobalMeanRegressor()
    b1.fit(X_train, y_train)
    b1_preds = b1.predict(X_test)
    b1_mae = float(mean_absolute_error(y_test, b1_preds))
    b1_rmse = float(root_mean_squared_error(y_test, b1_preds))
    b1_r2 = float(r2_score(y_test, b1_preds))

    evaluation_results["Baseline_1_Global_Mean"] = {
        "type": "Simple Heuristic",
        "description": f"Predicts constant training mean ({b1.mean_:.2f} Q/Acre)",
        "test_mae": round(b1_mae, 3),
        "test_rmse": round(b1_rmse, 3),
        "test_r2": round(b1_r2, 4),
    }

    # Baseline 2: Crop-Stratified Mean
    b2 = CropStratifiedMeanRegressor(crop_col="crop")
    b2.fit(X_train, y_train)
    b2_preds = b2.predict(X_test)
    b2_mae = float(mean_absolute_error(y_test, b2_preds))
    b2_rmse = float(root_mean_squared_error(y_test, b2_preds))
    b2_r2 = float(r2_score(y_test, b2_preds))

    evaluation_results["Baseline_2_Crop_Stratified_Mean"] = {
        "type": "Simple Heuristic",
        "description": f"Predicts crop mean (Wheat: {b2.crop_means_.get('Wheat', 0):.2f}, Mustard: {b2.crop_means_.get('Mustard', 0):.2f})",
        "test_mae": round(b2_mae, 3),
        "test_rmse": round(b2_rmse, 3),
        "test_r2": round(b2_r2, 4),
    }

    # --- 2. Evaluate ML Candidate Pipelines ---
    ml_models = {
        "Linear_Ridge": Ridge(alpha=1.0),
        "RandomForest": RandomForestRegressor(
            n_estimators=120, max_depth=12, random_state=random_state, n_jobs=-1
        ),
        "XGBoost": XGBRegressor(
            n_estimators=120,
            learning_rate=0.08,
            max_depth=5,
            random_state=random_state,
            n_jobs=-1,
        ),
    }

    best_pipeline = None
    best_model_name = None
    best_rmse = float("inf")

    kf = KFold(n_splits=5, shuffle=True, random_state=random_state)

    for name, regressor in ml_models.items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", get_preprocessor()),
                ("regressor", regressor),
            ]
        )

        # 5-Fold Cross-Validation on training split
        cv_mae_scores = -cross_val_score(
            pipeline, X_train, y_train, cv=kf, scoring="neg_mean_absolute_error", n_jobs=-1
        )
        cv_rmse_scores = -cross_val_score(
            pipeline, X_train, y_train, cv=kf, scoring="neg_root_mean_squared_error", n_jobs=-1
        )

        # Fit on full training split and evaluate on hold-out test split
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(root_mean_squared_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        # Relative error reduction over crop-stratified baseline
        mae_improvement_pct = round(((b2_mae - mae) / b2_mae) * 100, 1)
        rmse_improvement_pct = round(((b2_rmse - rmse) / b2_rmse) * 100, 1)

        evaluation_results[name] = {
            "type": "Machine Learning Pipeline",
            "test_mae": round(mae, 3),
            "test_rmse": round(rmse, 3),
            "test_r2": round(r2, 4),
            "cv_mae_mean": round(float(np.mean(cv_mae_scores)), 3),
            "cv_mae_std": round(float(np.std(cv_mae_scores)), 3),
            "cv_rmse_mean": round(float(np.mean(cv_rmse_scores)), 3),
            "cv_rmse_std": round(float(np.std(cv_rmse_scores)), 3),
            "mae_improvement_vs_crop_mean_pct": f"{mae_improvement_pct}%",
            "rmse_improvement_vs_crop_mean_pct": f"{rmse_improvement_pct}%",
        }

        print(
            f"[{name}] Test MAE: {mae:.3f} | RMSE: {rmse:.3f} | R²: {r2:.4f} "
            f"(Improvement vs Baseline 2: {mae_improvement_pct}%)"
        )

        if rmse < best_rmse:
            best_rmse = rmse
            best_model_name = name
            best_pipeline = pipeline

    # Export best pipeline artifact
    model_save_path = MODELS_DIR / "best_yield_pipeline.joblib"
    joblib.dump(best_pipeline, model_save_path)

    report = {
        "dataset": {
            "file": "data/processed/western_up_rabi_data.csv",
            "total_samples": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "target": TARGET_COLUMN,
            "target_unit": "Quintals / Acre",
            "numerical_features": NUMERICAL_FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
        },
        "benchmarks": evaluation_results,
        "selected_model": best_model_name,
        "limitations": [
            "Dataset is calibrated to Western UP district averages; does not represent sensor-verified plot ground truth.",
            "Post-sowing climate variables (March temperature, seasonal rainfall) must be treated as forecast scenarios when predicting at sowing time.",
            "Unobserved variables such as seed variety, disease severity, and soil electrical conductivity are not captured.",
        ],
    }

    report_path = MODELS_DIR / "evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved top model ({best_model_name}) to {model_save_path}")
    print(f"Saved evaluation report to {report_path}")
    return report


if __name__ == "__main__":
    run_reproducible_pipeline()
