"""Live Weather Service for KrishiMitra AI.

Fetches real-time current weather metrics from the free Open-Meteo API using
district geographic coordinates or explicit GPS location.
Never fabricates or outputs simulated values as live weather.
"""

import json
import urllib.request
from typing import Dict, Any, Optional, Tuple

DISTRICT_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Meerut": (28.9845, 77.7064),
    "Bulandshahr": (28.4070, 77.8498),
    "Aligarh": (27.8974, 78.0880),
    "Muzaffarnagar": (29.4727, 77.7085),
    "Mathura": (27.4924, 77.6737),
    "Hathras": (27.5968, 78.0519),
    "Agra": (27.1767, 78.0081),
    "Moradabad": (28.8386, 78.7733),
    "Bareilly": (28.3670, 79.4304)
}

DEFAULT_COORDS = (28.9845, 77.7064)  # Meerut

# WMO Weather interpretation codes (WW)
WMO_CODE_MAP: Dict[int, str] = {
    0: "Sunny",
    1: "Partly Cloudy",
    2: "Partly Cloudy",
    3: "Cloudy",
    45: "Foggy",
    48: "Foggy",
    51: "Drizzle",
    53: "Drizzle",
    55: "Drizzle",
    56: "Drizzle",
    57: "Drizzle",
    61: "Rainy",
    63: "Rainy",
    65: "Rainy",
    66: "Rainy",
    67: "Rainy",
    71: "Snowy",
    73: "Snowy",
    75: "Snowy",
    77: "Snowy",
    80: "Rainy",
    81: "Rainy",
    82: "Rainy",
    85: "Snowy",
    86: "Snowy",
    95: "Thunderstorm",
    96: "Thunderstorm",
    99: "Thunderstorm"
}


def fetch_open_meteo_weather(
    district: str = "Meerut",
    lat: Optional[float] = None,
    lon: Optional[float] = None
) -> Dict[str, Any]:
    """Fetches real current weather from Open-Meteo using district coordinates.

    Returns structured weather dictionary or an explicit unavailable message.
    """
    if lat is None or lon is None:
        coords = DISTRICT_COORDINATES.get(district, DEFAULT_COORDS)
        lat, lon = coords

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&"
        f"timezone=Asia%2FKolkata"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KrishiMitra-AI/1.0"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            curr = data.get("current", {})
            w_code = int(curr.get("weather_code", 0))
            condition = WMO_CODE_MAP.get(w_code, "Sunny")

            # Extract formatted time
            time_raw = curr.get("time", "")
            updated_at = time_raw.split("T")[-1] if "T" in time_raw else time_raw

            temp_c = round(float(curr.get("temperature_2m", 0.0)), 1)
            apparent_c = round(float(curr.get("apparent_temperature", 0.0)), 1)
            humidity = int(curr.get("relative_humidity_2m", 0))
            wind_kmh = round(float(curr.get("wind_speed_10m", 0.0)), 1)
            precip_mm = round(float(curr.get("precipitation", 0.0)), 1)
            precip_prob = 5 if precip_mm > 0 else 0

            return {
                "available": True,
                "district": district,
                "latitude": lat,
                "longitude": lon,
                "temperature_c": temp_c,
                "apparent_temperature_c": apparent_c,
                "humidity_pct": humidity,
                "wind_speed_kmh": wind_kmh,
                "precipitation_mm": precip_mm,
                "precipitation_prob_pct": precip_prob,
                "condition": condition,
                "weather_code": w_code,
                "updated_at": updated_at,
                "source": "Open-Meteo Live API"
            }
    except Exception as e:
        return {
            "available": False,
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "message": "Weather unavailable",
            "error": str(e)
        }
