"""Tests for KrishiMitra AI Live Weather Service (Open-Meteo Integration)."""

import unittest
from unittest.mock import patch, MagicMock
import io
import json

from src.weather.live_weather import (
    fetch_open_meteo_weather,
    DISTRICT_COORDINATES,
    WMO_CODE_MAP
)


class TestLiveWeather(unittest.TestCase):

    def test_district_coordinates_exist(self):
        """All 9 Western UP pilot districts must have valid geographic coordinates."""
        expected_districts = [
            "Meerut", "Bulandshahr", "Aligarh", "Muzaffarnagar",
            "Mathura", "Hathras", "Agra", "Moradabad", "Bareilly"
        ]
        for dist in expected_districts:
            self.assertIn(dist, DISTRICT_COORDINATES)
            lat, lon = DISTRICT_COORDINATES[dist]
            self.assertTrue(26.0 <= lat <= 31.0, f"Latitude {lat} out of range for {dist}")
            self.assertTrue(76.0 <= lon <= 81.0, f"Longitude {lon} out of range for {dist}")

    @patch("urllib.request.urlopen")
    def test_successful_weather_fetch_and_units(self, mock_urlopen):
        """Verify proper field extraction, condition translation, and unit consistency."""
        mock_response = MagicMock()
        mock_data = {
            "current": {
                "time": "2026-10-22T14:30",
                "temperature_2m": 24.4,
                "apparent_temperature": 25.1,
                "relative_humidity_2m": 58,
                "wind_speed_10m": 9.2,
                "precipitation": 0.0,
                "weather_code": 0
            }
        }
        mock_response.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = fetch_open_meteo_weather("Meerut")

        self.assertTrue(res["available"])
        self.assertEqual(res["district"], "Meerut")
        self.assertEqual(res["temperature_c"], 24.4)
        self.assertEqual(res["apparent_temperature_c"], 25.1)
        self.assertEqual(res["humidity_pct"], 58)
        self.assertEqual(res["wind_speed_kmh"], 9.2)
        self.assertEqual(res["precipitation_mm"], 0.0)
        self.assertEqual(res["precipitation_prob_pct"], 0)
        self.assertEqual(res["condition"], "Sunny")
        self.assertEqual(res["updated_at"], "14:30")
        self.assertEqual(res["source"], "Open-Meteo Live API")

    @patch("urllib.request.urlopen")
    def test_custom_gps_coordinates(self, mock_urlopen):
        """User GPS coordinates must override district coordinates."""
        mock_response = MagicMock()
        mock_data = {
            "current": {
                "time": "2026-10-22T15:00",
                "temperature_2m": 26.0,
                "apparent_temperature": 27.0,
                "relative_humidity_2m": 62,
                "wind_speed_10m": 12.0,
                "precipitation": 2.5,
                "weather_code": 61
            }
        }
        mock_response.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = fetch_open_meteo_weather("My Location", lat=28.5355, lon=77.3910)

        self.assertTrue(res["available"])
        self.assertEqual(res["district"], "My Location")
        self.assertEqual(res["latitude"], 28.5355)
        self.assertEqual(res["longitude"], 77.3910)
        self.assertEqual(res["temperature_c"], 26.0)
        self.assertEqual(res["condition"], "Rainy")
        self.assertEqual(res["precipitation_mm"], 2.5)
        self.assertEqual(res["precipitation_prob_pct"], 5)

    @patch("urllib.request.urlopen")
    def test_unavailable_fallback_never_fabricates_mock_data(self, mock_urlopen):
        """When weather API is unreachable, it must report 'Weather unavailable' without fake numbers."""
        mock_urlopen.side_effect = Exception("Connection refused / Network unreachable")

        res = fetch_open_meteo_weather("Meerut")

        self.assertFalse(res["available"])
        self.assertEqual(res["district"], "Meerut")
        self.assertEqual(res["message"], "Weather unavailable")
        self.assertNotIn("temperature_c", res)
        self.assertNotIn("wind_speed_kmh", res)

    def test_wmo_code_mappings(self):
        """Test WMO weather interpretation codes."""
        self.assertEqual(WMO_CODE_MAP[0], "Sunny")
        self.assertEqual(WMO_CODE_MAP[3], "Cloudy")
        self.assertEqual(WMO_CODE_MAP[61], "Rainy")
        self.assertEqual(WMO_CODE_MAP[95], "Thunderstorm")
        self.assertEqual(WMO_CODE_MAP[45], "Foggy")


if __name__ == "__main__":
    unittest.main()
