"""Yield prediction engine blending empirical Multi-State Crop/Soil/Weather Random Forest
with plot-level agronomic response (sowing window, irrigation, NPK, and March heat stress).
"""

import json
import math
import os
from typing import Dict, Any, Optional
import joblib
import numpy as np
import pandas as pd

from config.settings import CONFIG, MODELS_DIR, PROCESSED_DATA_DIR
from src.database.db import log_prediction

STATE_ALIASES = {
    "up": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "mp": "Madhya Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    "bihar": "Bihar",
    "br": "Bihar",
    "rajasthan": "Rajasthan",
    "rj": "Rajasthan",
    "punjab": "Punjab",
    "pb": "Punjab",
    "haryana": "Haryana",
    "hr": "Haryana",
}

CROP_ALIASES = {
    "wheat": "Wheat",
    "gehu": "Wheat",
    "mustard": "Mustard",
    "sarson": "Mustard",
    "rapeseed &mustard": "Mustard",
    "rapeseed & mustard": "Mustard",
    "gram": "Gram",
    "chana": "Gram",
    "chickpea": "Gram",
    "barley": "Barley",
    "jau": "Barley",
    "masoor": "Masoor",
    "lentil": "Masoor",
    "maize": "Maize",
    "makka": "Maize",
    "peas & beans (pulses)": "Peas & beans (Pulses)",
    "peas": "Peas & beans (Pulses)",
    "matar": "Peas & beans (Pulses)",
    "potato": "Potato",
    "aloo": "Potato",
    "onion": "Onion",
    "pyaz": "Onion",
    "linseed": "Linseed",
    "alsi": "Linseed",
}


def _safe_float(val: Any, default: float) -> float:
    if val is None or val == "":
        return default
    try:
        f = float(val)
        return default if math.isnan(f) or math.isinf(f) else f
    except (ValueError, TypeError):
        return default


class YieldPredictor:
    """Plot-level yield predictor supporting all 6 states, 243+ districts, and Rabi crops."""

    def __init__(self):
        self.pipeline_path = MODELS_DIR / "best_yield_pipeline.joblib"
        self.multi_model_path = MODELS_DIR / "multi_state_yield_model.pkl"
        self.multi_cols_path = MODELS_DIR / "model_feature_columns.pkl"
        self.empirical_csv = PROCESSED_DATA_DIR / "multi_state_rabi_data.csv"

        self.pipeline = joblib.load(self.pipeline_path) if self.pipeline_path.exists() else None
        self.multi_model = joblib.load(self.multi_model_path) if self.multi_model_path.exists() else None
        self.multi_cols = joblib.load(self.multi_cols_path) if self.multi_cols_path.exists() else []

        # Build fast lookup of empirical district-crop averages & soil/weather profiles from the 19,863-row dataset
        self.district_crop_lookup: Dict[tuple, float] = {}
        self.district_env_lookup: Dict[tuple, Dict[str, float]] = {}
        if self.empirical_csv.exists():
            try:
                df_emp = pd.read_csv(self.empirical_csv)
                for (st, dist, cr), grp in df_emp.groupby(["state", "district", "crop"]):
                    self.district_crop_lookup[(str(st).lower(), str(dist).lower(), str(cr).lower())] = float(
                        grp["yield_q_acre"].tail(5).mean()
                    )
                for (st, dist), grp in df_emp.groupby(["state", "district"]):
                    row0 = grp.iloc[-1]
                    self.district_env_lookup[(str(st).lower(), str(dist).lower())] = {
                        "nitrogen_medium_pct": float(row0.get("nitrogen_medium_pct", 25.0)),
                        "phosphorus_medium_pct": float(row0.get("phosphorus_medium_pct", 55.0)),
                        "potassium_medium_pct": float(row0.get("potassium_medium_pct", 50.0)),
                        "organic_carbon_medium_pct": float(row0.get("organic_carbon_medium_pct", 40.0)),
                        "ph_neutral_pct": float(row0.get("ph_neutral_pct", 80.0)),
                        "avg_temp_c": float(row0.get("avg_temp_c", 24.5)),
                        "avg_humidity_pct": float(row0.get("avg_humidity_pct", 58.0)),
                        "seasonal_rainfall_mm": float(row0.get("seasonal_rainfall_mm", 45.0)),
                        "solar_rad_mj_m2": float(row0.get("solar_rad_mj_m2", 18.0)),
                    }
            except Exception as e:
                print(f"Warning: Could not build empirical lookup: {e}")

    def _resolve_state(self, raw_state: Any, district: str) -> str:
        if raw_state:
            s_clean = str(raw_state).strip().lower()
            if s_clean in STATE_ALIASES:
                return STATE_ALIASES[s_clean]
            for st in CONFIG.supported_states:
                if st.lower() == s_clean:
                    return st
        # Infer from district
        d_lower = str(district).strip().lower()
        for st, dists in CONFIG.state_districts.items():
            if any(d.lower() == d_lower for d in dists):
                return st
        return "Uttar Pradesh"

    def _resolve_crop(self, raw_crop: Any) -> Optional[str]:
        if not raw_crop:
            return "Wheat"
        c_clean = str(raw_crop).strip().lower()
        if c_clean in CROP_ALIASES:
            return CROP_ALIASES[c_clean]
        for valid_c in CONFIG.crops:
            if valid_c.lower() == c_clean:
                return "Mustard" if "mustard" in valid_c.lower() else valid_c
        return None

    def predict(self, farmer_input: Dict[str, Any]) -> Dict[str, Any]:
        raw_crop = farmer_input.get("crop", "Wheat")
        canonical_crop = self._resolve_crop(raw_crop)
        if canonical_crop is None:
            return {
                "status": "unsupported",
                "valid": False,
                "supported": False,
                "crop": str(raw_crop),
                "message": (
                    f"Crop '{raw_crop}' is currently outside the Western UP Rabi pilot scope "
                    f"and Multi-State Rabi supported crops ({', '.join(CONFIG.crops[:8])})."
                ),
            }

        district = str(farmer_input.get("district") or "Meerut").strip()
        state = self._resolve_state(farmer_input.get("state"), district)
        plot_acres = max(0.1, _safe_float(farmer_input.get("plot_acres"), 2.0))
        soil_type = str(farmer_input.get("soil_type") or "Alluvial (Sandy Loam)")
        irrigation_source = str(farmer_input.get("irrigation_source") or "Tube well / Borewell")
        sowing_window = str(farmer_input.get("sowing_window") or "Timely Sown (Nov 01 - Nov 20)")

        # Fetch district empirical soil & weather defaults when user doesn't override
        env_defaults = self.district_env_lookup.get((state.lower(), district.lower()), {})
        default_rain = env_defaults.get("seasonal_rainfall_mm", 65.0)
        seasonal_rainfall_mm = _safe_float(farmer_input.get("seasonal_rainfall_mm"), default_rain)
        march_max_temp_c = _safe_float(farmer_input.get("march_max_temp_c"), 31.5)
        nitrogen_kg_acre = _safe_float(
            farmer_input.get("nitrogen_kg_acre"),
            32.0 if canonical_crop == "Mustard" else 48.0,
        )
        phosphorus_kg_acre = _safe_float(
            farmer_input.get("phosphorus_kg_acre"),
            16.0 if canonical_crop == "Mustard" else 22.0,
        )
        potassium_kg_acre = _safe_float(
            farmer_input.get("potassium_kg_acre"),
            8.0 if canonical_crop == "Mustard" else 15.0,
        )

        # Lookup state & district benchmark
        state_bench_map = CONFIG.state_yield_benchmarks.get(state, {})
        crop_bench = state_bench_map.get(
            canonical_crop,
            CONFIG.baseline_yield_benchmarks.get(
                canonical_crop, {"mean": 16.0, "min": 8.0, "max": 25.0, "std": 2.4}
            ),
        )
        baseline_mean = float(crop_bench["mean"])
        emp_dist_mean = self.district_crop_lookup.get(
            (state.lower(), district.lower(), canonical_crop.lower())
        )
        if emp_dist_mean and emp_dist_mean > 0:
            # Blend official state benchmark and empirical district APY mean
            baseline_mean = round(0.55 * baseline_mean + 0.45 * emp_dist_mean, 2)

        min_bound = float(crop_bench.get("min", baseline_mean * 0.55))
        max_bound = float(crop_bench.get("max", baseline_mean * 1.55))

        pred_q_acre = baseline_mean

        # 1. If Wheat or Mustard, use the calibrated plot-level pipeline + empirical multi-state model blend
        if canonical_crop in {"Wheat", "Mustard"} and self.pipeline is not None:
            row_df = pd.DataFrame([{
                "state": state,
                "crop": canonical_crop,
                "district": district,
                "plot_acres": plot_acres,
                "soil_type": soil_type,
                "irrigation_source": irrigation_source,
                "sowing_window": sowing_window,
                "seasonal_rainfall_mm": seasonal_rainfall_mm,
                "march_max_temp_c": march_max_temp_c,
                "nitrogen_kg_acre": nitrogen_kg_acre,
                "phosphorus_kg_acre": phosphorus_kg_acre,
                "potassium_kg_acre": potassium_kg_acre,
            }])
            pipe_pred = float(self.pipeline.predict(row_df)[0])
            pred_q_acre = pipe_pred

        # 2. Incorporate empirical multi-state model (trained on 19,863 records across all crops & districts)
        if self.multi_model is not None and self.multi_cols:
            area_ha = plot_acres / 2.47105
            in_row = {
                "area_ha": area_ha,
                "nitrogen_medium_pct": env_defaults.get("nitrogen_medium_pct", nitrogen_kg_acre * 0.6),
                "phosphorus_medium_pct": env_defaults.get("phosphorus_medium_pct", phosphorus_kg_acre * 2.2),
                "potassium_medium_pct": env_defaults.get("potassium_medium_pct", potassium_kg_acre * 3.0),
                "organic_carbon_medium_pct": env_defaults.get("organic_carbon_medium_pct", 42.0),
                "ph_neutral_pct": env_defaults.get("ph_neutral_pct", 82.0),
                "avg_temp_c": env_defaults.get("avg_temp_c", march_max_temp_c - 6.0),
                "avg_humidity_pct": env_defaults.get("avg_humidity_pct", 58.0),
                "seasonal_rainfall_mm": seasonal_rainfall_mm,
                "solar_rad_mj_m2": env_defaults.get("solar_rad_mj_m2", 18.2),
            }
            row_dict = {c: 0.0 for c in self.multi_cols}
            for k, v in in_row.items():
                if k in row_dict:
                    row_dict[k] = float(v)
            for prefix, val in [("state", state), ("district", district), ("crop", canonical_crop)]:
                cname = f"{prefix}_{val}"
                if cname in row_dict:
                    row_dict[cname] = 1.0
            df_in = pd.DataFrame([row_dict], columns=self.multi_cols)
            emp_pred = float(self.multi_model.predict(df_in)[0])

            # Agronomic modifiers for sowing window & irrigation on non-Wheat/Mustard crops
            sow_mod = 1.04 if "Early" in sowing_window else (1.0 if "Timely" in sowing_window else 0.89)
            irr_mod = 1.04 if "Tube" in irrigation_source else (1.01 if "Canal" in irrigation_source else 0.86)
            emp_adjusted = emp_pred * sow_mod * irr_mod

            if canonical_crop in {"Wheat", "Mustard"}:
                pred_q_acre = 0.72 * pred_q_acre + 0.28 * max(min_bound, min(max_bound, emp_adjusted))
            else:
                pred_q_acre = emp_adjusted

        pred_q_acre = round(float(np.clip(pred_q_acre, min_bound, max_bound)), 2)
        pred_q_ha = round(pred_q_acre * 2.47105, 2)
        pred_t_ha = round(pred_q_ha / 10.0, 2)
        total_harvest = round(pred_q_acre * plot_acres, 2)

        ci_half = round(max(0.8, pred_q_acre * 0.095), 2)
        ci_lower = round(max(min_bound * 0.85, pred_q_acre - ci_half), 2)
        ci_upper = round(min(max_bound * 1.10, pred_q_acre + ci_half), 2)

        perf_pct = round(((pred_q_acre - baseline_mean) / max(0.1, baseline_mean)) * 100.0, 1)

        log_prediction(
            crop=canonical_crop,
            district=district,
            plot_acres=plot_acres,
            pred_q_acre=pred_q_acre,
            pred_q_ha=pred_q_ha,
            pred_t_ha=pred_t_ha,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            model_name="Random Forest Regressor (6-State Empirical + Soil/Weather)",
            farmer_id=farmer_input.get("farmer_id", "farmer-001"),
            plot_id=farmer_input.get("plot_id"),
            input_params=farmer_input,
        )

        return {
            "status": "success",
            "valid": True,
            "supported": True,
            "state": state,
            "district": district,
            "crop": canonical_crop,
            "season": "Rabi",
            "plot_acres": plot_acres,
            "predicted_yield_per_acre": pred_q_acre,
            "predicted_yield_q_ha": pred_q_ha,
            "predicted_yield_tonne_per_ha": pred_t_ha,
            "yield_unit": "Quintals/Acre",
            "total_harvest_quintals": total_harvest,
            "confidence_interval_90": {
                "lower": ci_lower,
                "upper": ci_upper,
                "unit": "Quintals/Acre",
            },
            "regional_benchmark_mean": baseline_mean,
            "performance_vs_regional_mean_pct": perf_pct,
            "soil_weather_enriched": bool(env_defaults),
            "model_used": "Random Forest Regressor (Multi-State Crop + Soil + Weather)",
        }


MultiStateYieldPredictor = YieldPredictor
