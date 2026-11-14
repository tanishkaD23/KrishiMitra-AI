"""Configuration settings for KrishiMitra AI All-India agricultural platform."""
import json
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SCHEMES_DATA_DIR = DATA_DIR / "schemes"
MODELS_DIR = BASE_DIR / "models"

# Exact required All-India dataset paths
CROP_DATASET_PATH = BASE_DIR / "crops" / "all_india_all_seasons_crops_dataset(1).csv"
SOIL_DATASET_PATH = BASE_DIR / "soil" / "all_states_india_soil_dataset(2).csv"
WEATHER_DATASET_PATH = BASE_DIR / "weather" / "all_states_india_weather_and_rainfall_dataset(1).csv"


def _load_dynamic_coverage() -> Dict[str, Any]:
    """Loads All-India states, districts, crops, and seasons dynamically from the lookup/report."""
    lookup_path = MODELS_DIR / "all_india_intelligence_lookup.joblib"
    if lookup_path.exists():
        try:
            import joblib
            data = joblib.load(lookup_path)
            return {
                "states": data.get("all_states", []),
                "state_districts": data.get("state_districts", {}),
                "crops": data.get("all_crops", []),
                "seasons": data.get("all_seasons", ["Kharif", "Rabi", "Summer", "Winter", "Autumn"]),
                "state_crops": data.get("state_crops", {}),
                "state_seasons": data.get("state_seasons", {}),
                "district_crops": data.get("district_crops", {}),
                "crop_seasons": data.get("crop_seasons", {}),
            }
        except Exception:
            pass
    return {}


_DYN = _load_dynamic_coverage()


class PilotConfig(BaseModel):
    state: str = "Uttar Pradesh"
    region: str = "All-India Agricultural Intelligence & Decision Support Platform (35 States/UTs, 736 Districts)"
    season: str = "Rabi"
    yield_unit: str = "Tonnes/Hectare & Quintals/Acre"

    supported_states: List[str] = _DYN.get("states") or [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir",
        "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Madhya Pradesh",
        "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
        "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim",
        "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
        "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
        "Dadra and Nagar Haveli and Daman and Diu", "Delhi"
    ]

    state_districts: Dict[str, List[str]] = _DYN.get("state_districts") or {
        "Uttar Pradesh": [
            "Agra", "Aligarh", "Allahabad", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya", "Azamgarh",
            "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi",
            "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah",
            "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad",
            "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun",
            "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi",
            "Kheri (Lakhimpur)", "Kushinagar", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri",
            "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit",
            "Pratapgarh", "Prayagraj", "Raebareli", "Rampur", "Saharanpur", "Sambhal",
            "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti",
            "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"
        ],
    }

    state_crops: Dict[str, List[str]] = _DYN.get("state_crops") or {}
    state_seasons: Dict[str, List[str]] = _DYN.get("state_seasons") or {}
    district_crops: Dict[str, List[str]] = _DYN.get("district_crops") or {}
    crop_seasons: Dict[str, List[str]] = _DYN.get("crop_seasons") or {}
    all_india_crops: List[str] = _DYN.get("crops") or []

    districts: List[str] = [
        "Meerut", "Bulandshahr", "Aligarh", "Muzaffarnagar", "Mathura",
        "Hathras", "Agra", "Moradabad", "Bareilly", "Saharanpur",
        "Bijnor", "Lucknow", "Kanpur Nagar", "Varanasi", "Prayagraj",
        "Gorakhpur", "Jhansi", "Shahjahanpur", "Sitapur", "Hardoi"
    ]

    seasons: List[str] = _DYN.get("seasons") or ["Kharif", "Rabi", "Summer", "Winter", "Autumn"]

    crops: List[str] = (
        ["Wheat", "Mustard"]
        + [c for c in (_DYN.get("crops") or [
            "Rapeseed &Mustard", "Rice", "Maize", "Gram", "Barley", "Masoor",
            "Peas & beans (Pulses)", "Potato", "Onion", "Linseed", "Arhar/Tur",
            "Moong(Green Gram)", "Urad", "Groundnut", "Soyabean", "Sunflower",
            "Sesamum", "Jowar", "Bajra", "Ragi"
        ]) if c not in ("Wheat", "Mustard")]
    )

    soil_types: List[str] = [
        "Alluvial (Sandy Loam)",
        "Alluvial (Clay Loam)",
        "Loam",
        "Black Cotton Soil (Vertisol)",
        "Red & Lateritic Soil",
        "Arid Sandy Soil",
    ]

    irrigation_sources: List[str] = [
        "Tube well / Borewell",
        "Canal",
        "Canal Irrigation",
        "Rainfed",
        "Rainfed / Limited",
        "Drip / Micro-Irrigation",
    ]

    baseline_yield_benchmarks: Dict[str, Dict[str, float]] = {
        "Wheat": {"mean": 16.8, "min": 8.5, "max": 26.5, "std": 2.6},
        "Mustard": {"mean": 7.5, "min": 3.5, "max": 12.5, "std": 1.6},
        "Rapeseed &Mustard": {"mean": 7.5, "min": 3.5, "max": 12.5, "std": 1.6},
        "Rice": {"mean": 14.5, "min": 6.5, "max": 25.0, "std": 2.8},
        "Gram": {"mean": 5.2, "min": 2.5, "max": 10.5, "std": 1.4},
        "Barley": {"mean": 12.4, "min": 6.0, "max": 20.5, "std": 2.1},
        "Masoor": {"mean": 4.2, "min": 2.0, "max": 8.5, "std": 1.2},
        "Maize": {"mean": 15.2, "min": 7.0, "max": 28.0, "std": 3.1},
        "Peas & beans (Pulses)": {"mean": 5.8, "min": 2.5, "max": 11.5, "std": 1.5},
        "Potato": {"mean": 92.5, "min": 45.0, "max": 145.0, "std": 14.0},
        "Onion": {"mean": 62.0, "min": 30.0, "max": 110.0, "std": 11.0},
        "Linseed": {"mean": 3.6, "min": 1.5, "max": 7.5, "std": 1.0},
    }

    state_yield_benchmarks: Dict[str, Dict[str, Dict[str, float]]] = {
        "Uttar Pradesh": {
            "Wheat": {"mean": 16.8, "min": 10.0, "max": 24.5, "std": 2.8},
            "Mustard": {"mean": 7.5, "min": 4.0, "max": 11.5, "std": 1.6},
            "Gram": {"mean": 5.1, "min": 2.5, "max": 9.8, "std": 1.3},
            "Barley": {"mean": 12.2, "min": 6.5, "max": 19.0, "std": 2.0},
            "Masoor": {"mean": 4.1, "min": 2.0, "max": 8.0, "std": 1.1},
            "Potato": {"mean": 95.0, "min": 50.0, "max": 145.0, "std": 14.0},
        },
        "Madhya Pradesh": {
            "Wheat": {"mean": 15.4, "min": 9.5, "max": 22.0, "std": 2.7},
            "Mustard": {"mean": 6.8, "min": 3.8, "max": 10.5, "std": 1.5},
            "Gram": {"mean": 5.8, "min": 3.0, "max": 10.5, "std": 1.4},
            "Barley": {"mean": 10.8, "min": 5.5, "max": 17.5, "std": 1.9},
            "Masoor": {"mean": 4.5, "min": 2.2, "max": 8.5, "std": 1.2},
            "Potato": {"mean": 88.0, "min": 45.0, "max": 135.0, "std": 13.0},
        },
        "Bihar": {
            "Wheat": {"mean": 13.6, "min": 8.5, "max": 19.5, "std": 2.4},
            "Mustard": {"mean": 5.9, "min": 3.5, "max": 9.2, "std": 1.4},
            "Gram": {"mean": 4.6, "min": 2.2, "max": 8.8, "std": 1.2},
            "Barley": {"mean": 9.5, "min": 5.0, "max": 15.5, "std": 1.8},
            "Masoor": {"mean": 4.0, "min": 2.0, "max": 7.8, "std": 1.1},
            "Maize": {"mean": 16.5, "min": 8.5, "max": 28.0, "std": 3.2},
            "Potato": {"mean": 90.0, "min": 45.0, "max": 138.0, "std": 13.5},
        },
        "Rajasthan": {
            "Wheat": {"mean": 16.2, "min": 10.0, "max": 23.0, "std": 2.9},
            "Mustard": {"mean": 8.1, "min": 4.5, "max": 12.2, "std": 1.7},
            "Gram": {"mean": 5.0, "min": 2.5, "max": 9.5, "std": 1.4},
            "Barley": {"mean": 13.5, "min": 7.0, "max": 20.5, "std": 2.2},
        },
        "Punjab": {
            "Wheat": {"mean": 20.4, "min": 14.0, "max": 26.5, "std": 2.2},
            "Mustard": {"mean": 7.9, "min": 4.5, "max": 11.8, "std": 1.5},
            "Gram": {"mean": 5.6, "min": 3.0, "max": 9.8, "std": 1.3},
            "Barley": {"mean": 15.2, "min": 9.0, "max": 21.5, "std": 2.0},
            "Potato": {"mean": 98.0, "min": 55.0, "max": 148.0, "std": 13.0},
        },
        "Haryana": {
            "Wheat": {"mean": 19.6, "min": 13.5, "max": 25.8, "std": 2.3},
            "Mustard": {"mean": 8.4, "min": 4.8, "max": 12.5, "std": 1.6},
            "Gram": {"mean": 5.4, "min": 2.8, "max": 9.6, "std": 1.3},
            "Barley": {"mean": 14.8, "min": 8.5, "max": 21.0, "std": 2.1},
        },
    }


CONFIG = PilotConfig()
