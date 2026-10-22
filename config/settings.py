"""Configuration settings for KrishiMitra AI pilot prototype."""

from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SCHEMES_DATA_DIR = DATA_DIR / "schemes"
MODELS_DIR = BASE_DIR / "models"


class PilotConfig(BaseModel):
    state: str = "Uttar Pradesh"
    region: str = "Western Uttar Pradesh"
    districts: List[str] = [
        "Meerut",
        "Bulandshahr",
        "Aligarh",
        "Muzaffarnagar",
        "Mathura",
        "Hathras",
        "Agra",
        "Moradabad",
        "Bareilly",
    ]
    crops: List[str] = ["Wheat", "Mustard"]
    season: str = "Rabi"

    # Soil taxonomy for Western Gangetic Plains
    soil_types: List[str] = [
        "Alluvial (Sandy Loam)",
        "Alluvial (Clay Loam)",
        "Loam",
    ]

    # Irrigation taxonomy
    irrigation_sources: List[str] = [
        "Tube well / Borewell",
        "Canal",
        "Rainfed",
    ]

    # Yield unit: Quintals per Acre (typical smallholder reporting unit in North India)
    # 1 Quintal = 100 kg. 1 Hectare ≈ 2.471 Acres.
    yield_unit: str = "Quintals/Acre"

    # Baseline average yield benchmarks (Quintals/Acre) for Western UP
    baseline_yield_benchmarks: Dict[str, Dict[str, float]] = {
        "Wheat": {"mean": 18.5, "min": 10.0, "max": 26.0, "std": 3.2},
        "Mustard": {"mean": 7.5, "min": 3.5, "max": 12.0, "std": 1.8},
    }


# Singleton config instance
CONFIG = PilotConfig()
