"""Live Weather & 7-Day Agronomic Forecasting Service for KrishiMitra AI.

Fetches real-time current weather metrics and 7-day daily forecasts from the
free Open-Meteo API for all 243+ districts across Uttar Pradesh, Madhya Pradesh,
Bihar, Rajasthan, Punjab, and Haryana (or via explicit GPS coordinates).
Computes dynamic seasonal risk indicators (Heavy Rainfall, Drought, Pest/Disease,
and Heat Stress) directly from live forecast telemetry.
"""

from datetime import datetime
import json
import os
import re
import urllib.request
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd

from config.settings import BASE_DIR

DISTRICT_COORDINATES: Dict[str, Tuple[float, float]] = {
    # Uttar Pradesh
    "Meerut": (28.9845, 77.7064),
    "Bulandshahr": (28.4070, 77.8498),
    "Aligarh": (27.8974, 78.0880),
    "Muzaffarnagar": (29.4727, 77.7085),
    "Mathura": (27.4924, 77.6737),
    "Hathras": (27.5968, 78.0519),
    "Agra": (27.1767, 78.0081),
    "Moradabad": (28.8386, 78.7733),
    "Bareilly": (28.3670, 79.4304),
    "Saharanpur": (29.9680, 77.5510),
    "Bijnor": (29.3724, 78.1358),
    "Shahjahanpur": (27.8815, 79.9120),
    "Lucknow": (26.8467, 80.9462),
    "Kanpur Nagar": (26.4499, 80.3319),
    "Prayagraj": (25.4358, 81.8463),
    "Allahabad": (25.4358, 81.8463),
    "Varanasi": (25.3176, 82.9739),
    "Gorakhpur": (26.7606, 83.3732),
    "Jhansi": (25.4484, 78.5685),
    "Ayodhya": (26.7922, 82.1998),
    "Faizabad": (26.7922, 82.1998),
    "Sitapur": (27.5619, 80.6827),
    "Hardoi": (27.3944, 80.1311),
    # Madhya Pradesh
    "Bhopal": (23.2599, 77.4126),
    "Indore": (22.7196, 75.8577),
    "Ujjain": (23.1765, 75.7885),
    "Sehore": (23.2032, 77.0844),
    "Vidisha": (23.5251, 77.8081),
    "Narmadapuram": (22.7483, 77.7289),
    "Hoshangabad": (22.7483, 77.7289),
    "Gwalior": (26.2183, 78.1828),
    "Morena": (26.4947, 77.9940),
    "Bhind": (26.5647, 78.7871),
    "Jabalpur": (23.1815, 79.9864),
    "Sagar": (23.8388, 78.7378),
    "Dewas": (22.9676, 76.0534),
    "Rewa": (24.5362, 81.3037),
    # Bihar
    "Patna": (25.5941, 85.1376),
    "Gaya": (24.7914, 85.0002),
    "Muzaffarpur": (26.1197, 85.3910),
    "Bhagalpur": (25.2425, 86.9842),
    "Nalanda": (25.1357, 85.4439),
    "Rohtas": (24.9500, 84.0167),
    "Bhojpur": (25.5560, 84.6603),
    "Samastipur": (25.8629, 85.7810),
    "Begusarai": (25.4182, 86.1272),
    "Purnia": (25.7771, 87.4753),
    "Vaishali": (25.6838, 85.2140),
    "Darbhanga": (26.1542, 85.8918),
    "Saran": (25.7811, 84.7302),
    # Rajasthan
    "Jaipur": (26.9124, 75.7873),
    "Sri Ganganagar": (29.9038, 73.8772),
    "Ganganagar": (29.9038, 73.8772),
    "Hanumangarh": (29.5815, 74.3294),
    "Alwar": (27.5530, 76.6346),
    "Bharatpur": (27.2152, 77.5030),
    "Kota": (25.2138, 75.8648),
    "Bundi": (25.4305, 75.6499),
    "Baran": (25.1011, 76.5132),
    "Sikar": (27.6094, 75.1399),
    "Nagaur": (27.2038, 73.7339),
    "Jodhpur": (26.2389, 73.0243),
    "Udaipur": (24.5854, 73.7125),
    "Ajmer": (26.4499, 74.6399),
    # Punjab
    "Ludhiana": (30.9010, 75.8573),
    "Patiala": (30.3398, 76.3869),
    "Sangrur": (30.2458, 75.8421),
    "Bathinda": (30.2110, 74.9455),
    "Amritsar": (31.6340, 74.8723),
    "Jalandhar": (31.3260, 75.5762),
    "Moga": (30.8165, 75.1717),
    "Ferozepur": (30.9331, 74.6225),
    "Firozepur": (30.9331, 74.6225),
    "Gurdaspur": (32.0419, 75.4053),
    "Hoshiarpur": (31.5143, 75.9115),
    "Kapurthala": (31.3808, 75.3800),
    "Mansa": (29.9880, 75.3932),
    # Haryana
    "Karnal": (29.6857, 76.9905),
    "Kurukshetra": (29.9695, 76.8783),
    "Hisar": (29.1492, 75.7217),
    "Sirsa": (29.5349, 75.0282),
    "Ambala": (30.3782, 76.7767),
    "Panipat": (29.3909, 76.9635),
    "Sonipat": (28.9931, 77.0151),
    "Rohtak": (28.8955, 76.6066),
    "Jind": (29.3164, 76.3142),
    "Kaithal": (29.8015, 76.3996),
    "Fatehabad": (29.5152, 75.4555),
    "Bhiwani": (28.7975, 76.1322),
    "Yamunanagar": (30.1290, 77.2674),
}

# Load coordinates for all 241+ districts from `weather_rainfall_datasets.csv`
_WEATHER_CSV = BASE_DIR / "weather_rainfall_datasets.csv"
_EMPIRICAL_WEATHER_BACKUP: Dict[str, Dict[str, float]] = {}

if _WEATHER_CSV.exists():
    try:
        _df_w = pd.read_csv(
            _WEATHER_CSV,
            usecols=[
                "District",
                "Latitude",
                "Longitude",
                "Current_Temp_C",
                "Relative_Humidity_pct",
                "Wind_Speed_10m_ms",
                "Rainfall_Current_mm",
                "Rainfall_Rolling_Sum_7d_mm",
            ],
        )
        _df_w["District"] = _df_w["District"].apply(
            lambda x: re.sub(r"^\d+\.\s*", "", str(x)).strip().title()
        )
        for dist_name, grp in _df_w.groupby("District"):
            row_last = grp.iloc[-1]
            if dist_name not in DISTRICT_COORDINATES:
                DISTRICT_COORDINATES[dist_name] = (
                    round(float(row_last["Latitude"]), 4),
                    round(float(row_last["Longitude"]), 4),
                )
            _EMPIRICAL_WEATHER_BACKUP[dist_name.lower()] = {
                "temp_c": round(float(grp["Current_Temp_C"].tail(4).mean()), 1),
                "humidity": int(round(float(grp["Relative_Humidity_pct"].tail(4).mean()))),
                "wind_kmh": round(float(grp["Wind_Speed_10m_ms"].tail(4).mean()) * 3.6, 1),
                "rain_7d_mm": round(float(grp["Rainfall_Rolling_Sum_7d_mm"].tail(4).mean()), 1),
            }
    except Exception:
        pass

DEFAULT_COORDS = (28.9845, 77.7064)  # Meerut

# WMO Weather interpretation codes (WW)
WMO_CODE_MAP: Dict[int, str] = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Morning Fog",
    48: "Dense Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Freezing Drizzle",
    57: "Freezing Drizzle",
    61: "Light Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Rain",
    67: "Heavy Rain",
    71: "Light Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Rain Showers",
    81: "Moderate Showers",
    82: "Heavy Showers",
    85: "Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm & Hail",
    99: "Severe Hailstorm",
}

WMO_ICON_MAP: Dict[int, str] = {
    0: "☀️",
    1: "🌤️",
    2: "⛅",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌦️",
    53: "🌦️",
    55: "🌧️",
    61: "🌦️",
    63: "🌧️",
    65: "⛈️",
    80: "🌦️",
    81: "🌧️",
    82: "⛈️",
    95: "⛈️",
    96: "⛈️",
    99: "⛈️",
}


def _compute_agronomic_risks(
    temp_c: float,
    humidity_pct: int,
    rain_7d_mm: float,
    max_temp_7d_c: float,
    wind_kmh: float,
) -> Dict[str, Any]:
    """Computes live seasonal risk indicators from real-time & 7-day forecast metrics."""
    # 1. Heavy Rainfall Risk
    if rain_7d_mm >= 45.0:
        heavy_rain = {"level": "High Risk", "code": "high", "detail": f"{rain_7d_mm} mm forecast in 7 days"}
    elif rain_7d_mm >= 20.0:
        heavy_rain = {"level": "Moderate", "code": "moderate", "detail": f"{rain_7d_mm} mm expected"}
    else:
        heavy_rain = {"level": "Low Risk", "code": "low", "detail": f"{rain_7d_mm} mm in next 7 days"}

    # 2. Drought / Moisture Deficit Risk
    if rain_7d_mm < 1.0 and humidity_pct < 32 and max_temp_7d_c > 33.0:
        drought = {"level": "Moderate", "code": "moderate", "detail": "Low humidity & zero rainfall"}
    else:
        drought = {"level": "Low Risk", "code": "low", "detail": "Soil moisture stable"}

    # 3. Pest & Disease Risk (Yellow Rust / Aphids thrive in 14–24°C with high humidity > 65%)
    if (13.0 <= temp_c <= 25.0 and humidity_pct >= 68) or humidity_pct >= 78:
        pest = {"level": "Moderate", "code": "moderate", "detail": f"Humidity {humidity_pct}% favors rust/aphids"}
    elif humidity_pct >= 88:
        pest = {"level": "High Risk", "code": "high", "detail": f"High humidity ({humidity_pct}%)"}
    else:
        pest = {"level": "Low Risk", "code": "low", "detail": f"Humidity {humidity_pct}% within safe range"}

    # 4. Heat Stress Risk (Terminal heat above 32°C in Rabi)
    peak_t = max(temp_c, max_temp_7d_c)
    if peak_t >= 35.0:
        heat = {"level": "High Risk", "code": "high", "detail": f"Peak max {peak_t}°C (>35°C threshold)"}
    elif peak_t >= 31.5:
        heat = {"level": "Moderate", "code": "moderate", "detail": f"Max temp {peak_t}°C approaching 32°C"}
    else:
        heat = {"level": "Low Risk", "code": "low", "detail": f"Peak {peak_t}°C optimal for Rabi growth"}

    # Overall Risk Level
    codes = [heavy_rain["code"], drought["code"], pest["code"], heat["code"]]
    if "high" in codes:
        overall = "High"
        overall_sub = "Active weather alert in 7-day window"
    elif codes.count("moderate") >= 2:
        overall = "Moderate"
        overall_sub = "Monitor field moisture & pest scouting"
    else:
        overall = "Low"
        overall_sub = "Favorable conditions for crop growth"

    return {
        "overall_risk": overall,
        "overall_sub": overall_sub,
        "heavy_rainfall": heavy_rain,
        "drought": drought,
        "pest_risk": pest,
        "heat_stress": heat,
    }


def _resolve_coordinates(district: str) -> Tuple[float, float]:
    if district in DISTRICT_COORDINATES:
        return DISTRICT_COORDINATES[district]
    d_lower = str(district).strip().lower()
    for k, v in DISTRICT_COORDINATES.items():
        if k.lower() == d_lower:
            return v
    return DEFAULT_COORDS


def fetch_open_meteo_weather(
    district: str = "Meerut",
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> Dict[str, Any]:
    """Fetches real current weather + 7-day daily forecast from Open-Meteo API."""
    if lat is None or lon is None:
        lat, lon = _resolve_coordinates(district)

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,surface_pressure&"
        f"daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&"
        f"timezone=Asia%2FKolkata&forecast_days=7"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KrishiMitra-AI/2.0"})
        with urllib.request.urlopen(req, timeout=4.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            curr = data.get("current", {})
            daily = data.get("daily", {})

            w_code = int(curr.get("weather_code", 0))
            condition = WMO_CODE_MAP.get(w_code, "Clear Sky")
            icon = WMO_ICON_MAP.get(w_code, "☀️")

            time_raw = curr.get("time", "")
            updated_at = time_raw.split("T")[-1] if "T" in time_raw else time_raw

            temp_c = round(float(curr.get("temperature_2m", 24.0)), 1)
            apparent_c = round(float(curr.get("apparent_temperature", temp_c)), 1)
            humidity = int(curr.get("relative_humidity_2m", 55))
            wind_kmh = round(float(curr.get("wind_speed_10m", 8.0)), 1)
            pressure_hpa = round(float(curr.get("surface_pressure", 1012.0)), 1)
            precip_now_mm = round(float(curr.get("precipitation", 0.0)), 1)

            # Parse 7-Day Daily Forecast
            dates = daily.get("time", [])
            t_max_list = daily.get("temperature_2m_max", [])
            t_min_list = daily.get("temperature_2m_min", [])
            p_sum_list = daily.get("precipitation_sum", [])
            p_prob_list = daily.get("precipitation_probability_max", [])
            w_codes_daily = daily.get("weather_code", [])
            wind_max_list = daily.get("wind_speed_10m_max", [])

            forecast_7d: List[Dict[str, Any]] = []
            total_rain_7d = 0.0
            max_temp_7d = temp_c

            for idx in range(min(7, len(dates))):
                d_str = dates[idx]
                try:
                    dt_obj = datetime.strptime(d_str, "%Y-%m-%d")
                    day_short = dt_obj.strftime("%a, %d %b")
                except ValueError:
                    day_short = d_str

                d_code = int(w_codes_daily[idx]) if idx < len(w_codes_daily) and w_codes_daily[idx] is not None else 0
                d_tmax = round(float(t_max_list[idx]), 1) if idx < len(t_max_list) and t_max_list[idx] is not None else temp_c + 3
                d_tmin = round(float(t_min_list[idx]), 1) if idx < len(t_min_list) and t_min_list[idx] is not None else temp_c - 6
                d_rain = round(float(p_sum_list[idx]), 1) if idx < len(p_sum_list) and p_sum_list[idx] is not None else 0.0
                d_prob = int(p_prob_list[idx]) if idx < len(p_prob_list) and p_prob_list[idx] is not None else (40 if d_rain > 0 else 5)
                d_wind = round(float(wind_max_list[idx]), 1) if idx < len(wind_max_list) and wind_max_list[idx] is not None else wind_kmh

                total_rain_7d += d_rain
                if d_tmax > max_temp_7d:
                    max_temp_7d = d_tmax

                forecast_7d.append({
                    "date": d_str,
                    "day_label": "Today" if idx == 0 else day_short,
                    "weather_code": d_code,
                    "condition": WMO_CODE_MAP.get(d_code, "Clear Sky"),
                    "icon": WMO_ICON_MAP.get(d_code, "☀️"),
                    "temp_max_c": d_tmax,
                    "temp_min_c": d_tmin,
                    "precipitation_mm": d_rain,
                    "precipitation_prob_pct": d_prob,
                    "wind_max_kmh": d_wind,
                })

            total_rain_7d = round(total_rain_7d, 1)
            max_rain_prob = max([d["precipitation_prob_pct"] for d in forecast_7d], default=0)
            risks = _compute_agronomic_risks(temp_c, humidity, total_rain_7d, max_temp_7d, wind_kmh)

            return {
                "available": True,
                "is_live": True,
                "district": district,
                "latitude": lat,
                "longitude": lon,
                "temperature_c": temp_c,
                "apparent_temperature_c": apparent_c,
                "humidity_pct": humidity,
                "wind_speed_kmh": wind_kmh,
                "surface_pressure_hpa": pressure_hpa,
                "precipitation_mm": precip_now_mm,
                "rain_next_7d_mm": total_rain_7d,
                "precipitation_prob_pct": max_rain_prob,
                "condition": condition,
                "icon": icon,
                "weather_code": w_code,
                "updated_at": updated_at,
                "source": "Open-Meteo Live Meteorological Stream",
                "daily_forecast": forecast_7d,
                "risk_indicators": risks,
            }
    except Exception as e:
        # Fallback to district telemetry from `weather_rainfall_datasets.csv` if offline
        emp = _EMPIRICAL_WEATHER_BACKUP.get(str(district).strip().lower(), {
            "temp_c": 24.5,
            "humidity": 56,
            "wind_kmh": 9.2,
            "rain_7d_mm": 4.2,
        })
        risks = _compute_agronomic_risks(
            emp["temp_c"], emp["humidity"], emp["rain_7d_mm"], emp["temp_c"] + 3.5, emp["wind_kmh"]
        )
        return {
            "available": True,
            "is_live": False,
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "temperature_c": emp["temp_c"],
            "apparent_temperature_c": emp["temp_c"],
            "humidity_pct": emp["humidity"],
            "wind_speed_kmh": emp["wind_kmh"],
            "precipitation_mm": 0.0,
            "rain_next_7d_mm": emp["rain_7d_mm"],
            "precipitation_prob_pct": 10 if emp["rain_7d_mm"] > 0 else 0,
            "condition": "Clear Sky",
            "icon": "☀️",
            "weather_code": 0,
            "updated_at": datetime.now().strftime("%H:%M"),
            "source": "District Meteorological Station Telemetry",
            "daily_forecast": [],
            "risk_indicators": risks,
            "error": str(e),
        }
