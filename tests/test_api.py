"""Unit tests for FastAPI endpoints, database integration, and mobile farmer dashboard delivery."""

import unittest
from fastapi.testclient import TestClient
from src.api.main import app


class TestApiAndDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("status"), "ok")
        self.assertIn("SQLite", res.json().get("database", ""))

    def test_dashboard_route_serves_html(self):
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        content = res.text
        # Assert key accessibility and requirement markers
        self.assertIn("KrishiMitra", content)
        self.assertIn("dashboard.css", content)
        self.assertIn("dashboard.js", content)
        self.assertIn("pcNotificationBanner", content)
        self.assertIn("mNotificationBanner", content)
        self.assertIn("नमूना डेटा", content)  # Demo data badge
        self.assertIn("मॉडल एवं डेटा सीमाएं", content)  # Limitations
        self.assertIn("PM-KISAN", content)  # Schemes
        self.assertIn("कृषिसाथी", content)  # KrishiSathi voice assistant
        self.assertIn("dashMicBtn", content)  # Microphone touch target

    def test_plots_api(self):
        res = self.client.get("/api/plots")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertGreaterEqual(len(data.get("plots", [])), 3)

    def test_yield_history_api(self):
        res = self.client.get("/api/yield-history?district=Meerut&crop=Wheat")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertGreater(data.get("records_count", 0), 0)

    def test_dashboard_data_composite_api(self):
        res = self.client.get("/api/dashboard-data?district=Meerut&crop=Wheat")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("farmer", data)
        self.assertIn("plots", data)
        self.assertIn("prediction", data)
        self.assertIn("historical_yields", data)
        self.assertIn("forecast_points", data)
        self.assertIn("weather", data)
        self.assertEqual(data["farmer"]["name"], "Tanishka")

    def test_analyze_api_flow(self):
        payload = {
            "crop": "Wheat",
            "district": "Meerut",
            "plot_acres": 2.0,
            "soil_type": "Alluvial (Sandy Loam)",
            "irrigation_source": "Tube well / Borewell",
            "sowing_window": "Timely Sown (Nov 01 - Nov 20)",
            "seasonal_rainfall_mm": 65.0,
            "march_max_temp_c": 31.5,
            "nitrogen_kg_acre": 48.0,
            "phosphorus_kg_acre": 22.0,
            "potassium_kg_acre": 15.0,
            "state": "Uttar Pradesh"
        }
        res = self.client.post("/api/analyze", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("yield", data)
        self.assertIn("advisory", data)
        self.assertIn("schemes", data)
        self.assertGreater(data["yield"]["predicted_yield_per_acre"], 10.0)

    def test_unsupported_crop_handling(self):
        payload = {
            "crop": "Sugarcane",
            "district": "Meerut",
            "plot_acres": 2.0
        }
        res = self.client.post("/api/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "unsupported")
        self.assertFalse(data.get("valid"))
        self.assertIn("outside the Western UP Rabi pilot scope", data.get("message", ""))

    def test_model_summary_api(self):
        res = self.client.get("/api/model-summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("models", data)
        self.assertIn("dataset_summary", data)
        self.assertEqual(data["dataset_summary"]["best_method_by_MAE"], "Previous-Year Baseline")
        self.assertEqual(len(data["models"]), 4)

    def test_model_summary_route_serves_html(self):
        res = self.client.get("/model-summary")
        self.assertEqual(res.status_code, 200)
        content = res.text
        self.assertIn("Model Performance & Benchmark Summary", content)
        self.assertIn("Previous-Year Baseline", content)
        self.assertIn("model-summary.css", content)
        self.assertIn("model-summary.js", content)

    def test_advisory_post_api(self):
        payload = {
            "crop": "Wheat",
            "district": "Meerut",
            "growth_stage": "Crown Root Initiation (CRI)",
            "reported_symptoms": ["yellow powder on leaves", "stripes"]
        }
        res = self.client.post("/api/advisory", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("structured_cards", data)
        self.assertGreaterEqual(len(data["structured_cards"]), 3)
        # Check that rust symptom generated evidence-based protocol
        rust_cards = [c for c in data["structured_cards"] if "rust" in c["id"]]
        self.assertEqual(len(rust_cards), 1)
        self.assertEqual(rust_cards[0]["priority"], "urgent")
        self.assertIn("wipe test", rust_cards[0]["recommendation"].lower())

    def test_advisory_get_api(self):
        res = self.client.get("/api/advisory?crop=Mustard&stage=Flowering")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("crop"), "Mustard")
        cards = data.get("structured_cards", [])
        self.assertGreaterEqual(len(cards), 2)

    def test_dashboard_data_with_stage_and_symptoms(self):
        res = self.client.get("/api/dashboard-data?district=Meerut&crop=Wheat&stage=Milking&symptoms=aphids")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        adv = data.get("advisory", {})
        cards = adv.get("structured_cards", [])
        self.assertTrue(any("grainfill" in c["id"] or "milking" in c["title_en"].lower() for c in cards))
        self.assertTrue(any("aphid" in c["id"] for c in cards))

    def test_live_weather_api(self):
        res = self.client.get("/api/weather?district=Meerut")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("available", data)
        if data.get("available"):
            self.assertIn("temperature_c", data)
            self.assertIn("humidity_pct", data)
            self.assertIn("wind_speed_kmh", data)
            self.assertIn("condition", data)
            self.assertEqual(data["district"], "Meerut")


if __name__ == "__main__":
    unittest.main()
