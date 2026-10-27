"""Unit tests for Flask application backend and dashboard integration."""

import json
import unittest
from src.api.flask_app import app


class TestFlaskApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("backend"), "Flask")

    def test_dashboard_route_serves_html(self):
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        content = res.get_data(as_text=True)
        self.assertIn("KrishiMitra", content)
        self.assertIn("krishimitra_pro.css", content)
        self.assertIn("dashboard.js", content)
        self.assertIn("PM Kisan", content)
        self.assertIn("KrishiSathi", content)

    def test_model_summary_route(self):
        res = self.client.get("/model-summary")
        self.assertEqual(res.status_code, 200)
        content = res.get_data(as_text=True)
        self.assertIn("Model Performance & Benchmark Summary", content)

    def test_get_plots_api(self):
        res = self.client.get("/api/plots")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertGreaterEqual(len(data.get("plots", [])), 3)

    def test_create_plot_api(self):
        payload = {
            "name": "Flask Test Plot",
            "crop": "Wheat",
            "acres": 3.0,
            "district": "Meerut"
        }
        res = self.client.post("/api/plots", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data["plot"]["name"], "Flask Test Plot")

    def test_yield_history_api(self):
        res = self.client.get("/api/yield-history?district=Meerut&crop=Wheat")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertGreater(data.get("records_count", 0), 0)

    def test_dashboard_data_composite_api(self):
        res = self.client.get("/api/dashboard-data?district=Meerut&crop=Wheat")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("farmer", data)
        self.assertIn("plots", data)
        self.assertIn("prediction", data)
        self.assertIn("historical_yields", data)
        self.assertIn("forecast_points", data)
        self.assertIn("weather", data)
        self.assertIn("advisory", data)
        self.assertIn("schemes", data)
        self.assertEqual(data["farmer"]["name"], "Tanishka")

    def test_predict_supported_crop(self):
        payload = {
            "crop": "Wheat",
            "district": "Meerut",
            "plot_acres": 2.5
        }
        res = self.client.post("/api/predict", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertTrue(data.get("supported"))
        self.assertGreater(data.get("predicted_yield_per_acre", 0), 10.0)

    def test_predict_unsupported_crop_safely_handled(self):
        payload = {
            "crop": "Cotton",
            "district": "Meerut",
            "plot_acres": 2.0
        }
        res = self.client.post("/api/predict", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "unsupported")
        self.assertFalse(data.get("valid"))
        self.assertIn("outside the Western UP Rabi pilot scope", data.get("message", ""))

    def test_advisory_flask_endpoint(self):
        payload = {
            "crop": "Wheat",
            "district": "Meerut",
            "growth_stage": "Tillering",
            "reported_symptoms": ["yellow powder"]
        }
        # POST
        res = self.client.post("/api/advisory", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("structured_cards", data)
        self.assertTrue(any("rust" in c["id"] for c in data["structured_cards"]))

        # GET
        res_get = self.client.get("/api/advisory?crop=Wheat&stage=CRI")
        self.assertEqual(res_get.status_code, 200)
        data_get = res_get.get_json()
        self.assertEqual(data_get.get("status"), "success")
        self.assertTrue(any("cri" in c["id"] for c in data_get["structured_cards"]))

    def test_live_weather_flask_api(self):
        res = self.client.get("/api/weather?district=Meerut")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("available", data)
        if data.get("available"):
            self.assertIn("temperature_c", data)
            self.assertIn("humidity_pct", data)
            self.assertIn("wind_speed_kmh", data)
            self.assertIn("condition", data)
            self.assertEqual(data["district"], "Meerut")


if __name__ == "__main__":
    unittest.main()
