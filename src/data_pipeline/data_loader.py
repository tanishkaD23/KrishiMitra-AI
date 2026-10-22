"""Data loader and benchmark dataset generator for Western UP Rabi crops (Wheat & Mustard)."""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple
from config.settings import CONFIG, PROCESSED_DATA_DIR


def generate_western_up_rabi_dataset(
    n_samples: int = 1500, random_seed: int = 42
) -> pd.DataFrame:
    """Generates a realistic agronomic dataset modeled on Western Uttar Pradesh

    historical Rabi seasons (Wheat & Mustard), reflecting realistic agro-climatic
    factors: terminal heat stress, irrigation access, soil loam textures, and NPK balance.
    """
    np.random.seed(random_seed)

    districts = CONFIG.districts
    soil_types = CONFIG.soil_types
    irrigation_sources = CONFIG.irrigation_sources
    sowing_windows = [
        "Early Rabi (Oct 15 - Oct 31)",
        "Timely Sown (Nov 01 - Nov 20)",
        "Late Sown (Nov 21 - Dec 15)",
    ]

    records = []

    for _ in range(n_samples):
        crop = np.random.choice(["Wheat", "Mustard"], p=[0.65, 0.35])
        district = np.random.choice(districts)
        soil = np.random.choice(
            soil_types, p=[0.45, 0.35, 0.20]
        )  # Sandy loam is most common in Doab
        irrigation = np.random.choice(
            irrigation_sources, p=[0.75, 0.20, 0.05]
        )  # Tubewells dominate Western UP
        sowing = np.random.choice(sowing_windows, p=[0.25, 0.55, 0.20])

        # Plot size in acres (log-normal distribution skewed towards marginal smallholders)
        plot_acres = float(np.clip(np.random.lognormal(mean=0.8, sigma=0.6), 0.5, 12.0))

        # Seasonal cumulative rainfall (mm) for Western UP Rabi (typically 30 - 110 mm)
        seasonal_rainfall_mm = float(np.random.normal(loc=65.0, scale=20.0))
        seasonal_rainfall_mm = max(10.0, seasonal_rainfall_mm)

        # Average Max Temperature in March (°C) - Critical for terminal heat stress in Wheat
        march_max_temp_c = float(np.random.normal(loc=31.5, scale=2.5))

        if crop == "Wheat":
            # Recommended N-P-K (kg/acre): ~50-24-16
            n_applied_kg = float(np.random.normal(loc=48.0, scale=8.0))
            p_applied_kg = float(np.random.normal(loc=22.0, scale=4.0))
            k_applied_kg = float(np.random.normal(loc=14.0, scale=3.0))

            # Base yield for Timely Sown Irrigated Wheat in Western UP ~ 18.5 Q/Acre (~4.5 tonnes/ha)
            base_yield = 18.5

            # Soil modifier
            soil_modifier = (
                0.8
                if "Clay Loam" in soil
                else (0.0 if "Sandy Loam" in soil else -0.5)
            )

            # Irrigation modifier
            irrigation_modifier = (
                0.5
                if "Tube well" in irrigation
                else (0.2 if "Canal" in irrigation else -4.5)
            )

            # Sowing penalty (late sowing reduces Wheat grain-filling window due to March heat)
            sowing_modifier = (
                0.4
                if "Early" in sowing
                else (0.0 if "Timely" in sowing else -2.8)
            )

            # Terminal heat penalty (March max temp > 33°C causes significant yield loss)
            heat_penalty = (
                max(0.0, march_max_temp_c - 32.0) * -1.2
                if march_max_temp_c > 32.0
                else 0.0
            )

            # Nitrogen response
            n_effect = np.clip((n_applied_kg - 40.0) * 0.12, -2.0, 2.0)

            noise = np.random.normal(0, 1.1)
            yield_val = (
                base_yield
                + soil_modifier
                + irrigation_modifier
                + sowing_modifier
                + heat_penalty
                + n_effect
                + noise
            )
            yield_val = np.clip(yield_val, 8.0, 26.5)

        else:  # Mustard
            # Mustard has lower nutrient and water requirement than wheat
            n_applied_kg = float(np.random.normal(loc=32.0, scale=6.0))
            p_applied_kg = float(np.random.normal(loc=16.0, scale=3.0))
            k_applied_kg = float(np.random.normal(loc=8.0, scale=2.0))

            # Base yield for Mustard in Western UP ~ 7.5 Q/Acre (~1.8 tonnes/ha)
            base_yield = 7.5

            # Early sowing is best for mustard to escape aphid attacks (Mahun)
            sowing_modifier = (
                0.9
                if "Early" in sowing
                else (0.0 if "Timely" in sowing else -2.2)
            )

            irrigation_modifier = (
                0.3
                if "Tube well" in irrigation
                else (0.0 if "Canal" in irrigation else -1.8)
            )
            soil_modifier = (
                0.5
                if "Sandy Loam" in soil
                else (0.0 if "Loam" in soil else -0.4)
            )

            # High humidity or late frost can impact mustard
            rain_effect = (
                -0.8
                if seasonal_rainfall_mm > 100.0
                else (0.4 if 40 <= seasonal_rainfall_mm <= 80 else -0.3)
            )

            noise = np.random.normal(0, 0.7)
            yield_val = (
                base_yield
                + sowing_modifier
                + irrigation_modifier
                + soil_modifier
                + rain_effect
                + noise
            )
            yield_val = np.clip(yield_val, 3.0, 12.5)

        records.append(
            {
                "crop": crop,
                "district": district,
                "plot_acres": round(plot_acres, 2),
                "soil_type": soil,
                "irrigation_source": irrigation,
                "sowing_window": sowing,
                "seasonal_rainfall_mm": round(seasonal_rainfall_mm, 1),
                "march_max_temp_c": round(march_max_temp_c, 1),
                "nitrogen_kg_acre": round(n_applied_kg, 1),
                "phosphorus_kg_acre": round(p_applied_kg, 1),
                "potassium_kg_acre": round(k_applied_kg, 1),
                "yield_quintals_per_acre": round(float(yield_val), 2),
            }
        )

    df = pd.DataFrame(records)
    return df


def load_or_generate_dataset(csv_name: str = "western_up_rabi_data.csv") -> pd.DataFrame:
    """Loads existing processed dataset or generates a clean benchmark dataset."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    target_path = PROCESSED_DATA_DIR / csv_name

    if target_path.exists():
        return pd.read_csv(target_path)

    df = generate_western_up_rabi_dataset(n_samples=2000)
    df.to_csv(target_path, index=False)
    return df


if __name__ == "__main__":
    df = load_or_generate_dataset()
    print(f"Dataset successfully created with shape: {df.shape}")
    print(df.head())
