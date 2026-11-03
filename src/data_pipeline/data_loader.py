"""Data loader and benchmark dataset generator for Multi-State Rabi crops (Wheat & Mustard).

Covers 6 major Rabi states:
- Uttar Pradesh (Updated full-state coverage)
- Madhya Pradesh
- Bihar
- Rajasthan
- Punjab
- Haryana
"""

import numpy as np
import pandas as pd
from pathlib import Path
from config.settings import CONFIG, PROCESSED_DATA_DIR


def generate_western_up_rabi_dataset(
    n_samples: int = 2400, random_seed: int = 42
) -> pd.DataFrame:
    """Generates a multi-state agronomic dataset modeled across Uttar Pradesh,
    Madhya Pradesh, Bihar, Rajasthan, Punjab, and Haryana for Rabi seasons
    (Wheat & Mustard), reflecting state-specific agro-climatic baselines,
    terminal heat stress, irrigation access, soil textures, and NPK balance.
    """
    np.random.seed(random_seed)

    states = CONFIG.supported_states
    state_weights = [0.30, 0.16, 0.14, 0.14, 0.13, 0.13]  # UP largest share
    soil_types = [
        "Alluvial (Sandy Loam)",
        "Alluvial (Clay Loam)",
        "Loam",
        "Black Cotton Soil (Vertisol)",
        "Arid Sandy Soil",
    ]
    irrigation_sources = [
        "Tube well / Borewell",
        "Canal",
        "Rainfed",
    ]
    sowing_windows = [
        "Early Rabi (Oct 15 - Oct 31)",
        "Timely Sown (Nov 01 - Nov 20)",
        "Late Sown (Nov 21 - Dec 15)",
    ]

    records = []

    for _ in range(n_samples):
        state = str(np.random.choice(states, p=state_weights))
        state_dists = CONFIG.state_districts.get(state, CONFIG.districts)
        district = str(np.random.choice(state_dists))
        crop = str(np.random.choice(["Wheat", "Mustard"], p=[0.65, 0.35]))

        if state == "Madhya Pradesh":
            soil = str(np.random.choice(soil_types, p=[0.20, 0.25, 0.20, 0.30, 0.05]))
        elif state == "Rajasthan":
            soil = str(np.random.choice(soil_types, p=[0.35, 0.10, 0.15, 0.05, 0.35]))
        else:
            soil = str(np.random.choice(soil_types, p=[0.45, 0.32, 0.18, 0.03, 0.02]))

        irrigation = str(np.random.choice(irrigation_sources, p=[0.72, 0.22, 0.06]))
        sowing = str(np.random.choice(sowing_windows, p=[0.25, 0.55, 0.20]))

        plot_acres = float(np.clip(np.random.lognormal(mean=0.85, sigma=0.6), 0.5, 15.0))
        seasonal_rainfall_mm = max(10.0, float(np.random.normal(loc=62.0, scale=20.0)))
        march_max_temp_c = float(np.random.normal(loc=31.5, scale=2.4))

        state_bench = CONFIG.state_yield_benchmarks.get(state, {}).get(crop)
        base_yield = state_bench["mean"] if state_bench else (18.0 if crop == "Wheat" else 7.5)

        if crop == "Wheat":
            n_applied_kg = float(np.random.normal(loc=48.0, scale=8.0))
            p_applied_kg = float(np.random.normal(loc=22.0, scale=4.0))
            k_applied_kg = float(np.random.normal(loc=14.0, scale=3.0))

            soil_modifier = (
                0.7 if "Clay Loam" in soil or "Black" in soil
                else (0.1 if "Sandy Loam" in soil else -0.6)
            )
            irrigation_modifier = (
                0.6 if "Tube well" in irrigation
                else (0.3 if "Canal" in irrigation else -4.2)
            )
            sowing_modifier = (
                0.4 if "Early" in sowing
                else (0.0 if "Timely" in sowing else -2.6)
            )
            heat_penalty = (
                max(0.0, march_max_temp_c - 32.0) * -1.15
                if march_max_temp_c > 32.0
                else 0.0
            )
            n_effect = float(np.clip((n_applied_kg - 42.0) * 0.11, -2.0, 2.0))
            noise = float(np.random.normal(0, 0.95))

            yield_val = (
                base_yield
                + soil_modifier
                + irrigation_modifier
                + sowing_modifier
                + heat_penalty
                + n_effect
                + noise
            )
            yield_val = float(np.clip(yield_val, 8.0, 26.0))
        else:
            n_applied_kg = float(np.random.normal(loc=32.0, scale=6.0))
            p_applied_kg = float(np.random.normal(loc=16.0, scale=3.0))
            k_applied_kg = float(np.random.normal(loc=8.0, scale=2.0))

            sowing_modifier = (
                0.8 if "Early" in sowing
                else (0.0 if "Timely" in sowing else -2.0)
            )
            irrigation_modifier = (
                0.35 if "Tube well" in irrigation
                else (0.1 if "Canal" in irrigation else -1.6)
            )
            soil_modifier = (
                0.45 if "Sandy Loam" in soil
                else (0.0 if "Loam" in soil else -0.35)
            )
            rain_effect = (
                -0.7 if seasonal_rainfall_mm > 100.0
                else (0.35 if 40 <= seasonal_rainfall_mm <= 80 else -0.25)
            )
            noise = float(np.random.normal(0, 0.65))

            yield_val = (
                base_yield
                + sowing_modifier
                + irrigation_modifier
                + soil_modifier
                + rain_effect
                + noise
            )
            yield_val = float(np.clip(yield_val, 3.5, 12.0))

        records.append(
            {
                "state": state,
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

    return pd.DataFrame(records)


def load_or_generate_dataset(
    csv_name: str = "western_up_rabi_data.csv", force_regenerate: bool = False
) -> pd.DataFrame:
    """Loads existing processed multi-state dataset or regenerates if state coverage is missing."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    target_path = PROCESSED_DATA_DIR / csv_name

    if target_path.exists() and not force_regenerate:
        df = pd.read_csv(target_path)
        if "state" in df.columns and df["state"].nunique() >= 6:
            return df

    df = generate_western_up_rabi_dataset(n_samples=2400)
    df.to_csv(target_path, index=False)
    return df


if __name__ == "__main__":
    df = load_or_generate_dataset(force_regenerate=True)
    print(f"Multi-state dataset created with shape: {df.shape}")
    print("State counts:\n", df["state"].value_counts())
