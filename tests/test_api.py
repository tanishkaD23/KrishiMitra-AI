"""Unit tests for FastAPI endpoints, database integration, and mobile farmer dashboard delivery."""

import unittest
from pathlib import Path
from src.api.main import (
    app,
    health_check,
    list_plots,
    get_history,
    get_dashboard_data,
    analyze_plot,
    predict_yield,
    get_model_summary,
    post_advisory,
    get_advisory_endpoint,
    get_weather,
    FarmerPlotInput,
    AdvisoryInput,
    FRONTEND_DIR
)


class TestApiAndDashboard(unittest.TestCase):

    def test_health_check(self):
        res = health_check()
        self.assertEqual(res.get("status"), "ok")
        self.assertIn("SQLite", res.get("database", ""))

    def test_dashboard_route_serves_html(self):
        dashboard_path = FRONTEND_DIR / "dashboard.html"
        self.assertTrue(dashboard_path.exists())
        content = dashboard_path.read_text(encoding="utf-8")
        self.assertIn("KrishiMitra", content)
        self.assertIn("krishimitra_pro.css", content)
        self.assertIn("dashboard.js", content)
        self.assertIn("PM Kisan", content)
        self.assertIn("KrishiSathi", content)

    def test_plots_api(self):
        res = list_plots("farmer-001")
        self.assertEqual(res.get("status"), "success")
        self.assertGreaterEqual(len(res.get("plots", [])), 3)

    def test_yield_history_api(self):
        res = get_history(district="Meerut", crop="Wheat")
        self.assertEqual(res.get("status"), "success")
        self.assertGreater(res.get("records_count", 0), 0)

    def test_dashboard_data_composite_api(self):
        data = get_dashboard_data(district="Meerut", crop="Wheat")
        self.assertEqual(data.get("status"), "success")
        self.assertIn("farmer", data)
        self.assertIn("plots", data)
        self.assertIn("prediction", data)
        self.assertIn("historical_yields", data)
        self.assertIn("forecast_points", data)
        self.assertIn("weather", data)
        self.assertEqual(data["farmer"]["name"], "Tanishka")

    def test_analyze_api_flow(self):
        payload = FarmerPlotInput(
            crop="Wheat",
            district="Meerut",
            plot_acres=2.0,
            soil_type="Alluvial (Sandy Loam)",
            irrigation_source="Tube well / Borewell",
            sowing_window="Timely Sown (Nov 01 - Nov 20)",
            seasonal_rainfall_mm=65.0,
            march_max_temp_c=31.5,
            nitrogen_kg_acre=48.0,
            phosphorus_kg_acre=22.0,
            potassium_kg_acre=15.0,
            state="Uttar Pradesh"
        )
        data = analyze_plot(payload)
        self.assertEqual(data.get("status"), "success")
        self.assertIn("yield", data)
        self.assertIn("advisory", data)
        self.assertIn("schemes", data)
        self.assertGreater(data["yield"]["predicted_yield_per_acre"], 10.0)

    def test_unsupported_crop_handling(self):
        payload = FarmerPlotInput(
            crop="Sugarcane",
            district="Meerut",
            plot_acres=2.0
        )
        data = predict_yield(payload)
        self.assertEqual(data.get("status"), "unsupported")
        self.assertFalse(data.get("valid"))
        self.assertIn("outside the Western UP Rabi pilot scope", data.get("message", ""))

    def test_model_summary_api(self):
        data = get_model_summary()
        self.assertIn("models", data)
        self.assertIn("dataset_summary", data)
        self.assertEqual(data["dataset_summary"]["best_method_by_MAE"], "Previous-Year Baseline")
        self.assertEqual(len(data["models"]), 4)

    def test_advisory_post_api(self):
        payload = AdvisoryInput(
            crop="Wheat",
            district="Meerut",
            growth_stage="Crown Root Initiation (CRI)",
            reported_symptoms=["yellow powder on leaves", "stripes"]
        )
        data = post_advisory(payload)
        self.assertEqual(data.get("status"), "success")
        self.assertIn("structured_cards", data)
        self.assertGreaterEqual(len(data["structured_cards"]), 3)
        rust_cards = [c for c in data["structured_cards"] if "rust" in c["id"]]
        self.assertEqual(len(rust_cards), 1)
        self.assertEqual(rust_cards[0]["priority"], "urgent")
        self.assertIn("wipe test", rust_cards[0]["recommendation"].lower())

    def test_advisory_get_api(self):
        data = get_advisory_endpoint(crop="Mustard", stage="Flowering")
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("crop"), "Mustard")
        cards = data.get("structured_cards", [])
        self.assertGreaterEqual(len(cards), 2)

    def test_dashboard_data_with_stage_and_symptoms(self):
        data = get_dashboard_data(district="Meerut", crop="Wheat", stage="Milking", symptoms="aphids")
        self.assertEqual(data.get("status"), "success")
        adv = data.get("advisory", {})
        cards = adv.get("structured_cards", [])
        self.assertTrue(any("grainfill" in c["id"] or "milking" in c["title_en"].lower() for c in cards))
        self.assertTrue(any("aphid" in c["id"] for c in cards))

    def test_live_weather_api(self):
        data = get_weather(district="Meerut")
        self.assertIn("available", data)
        if data.get("available"):
            self.assertIn("temperature_c", data)
            self.assertIn("humidity_pct", data)
            self.assertIn("wind_speed_kmh", data)
            self.assertIn("condition", data)
            self.assertEqual(data["district"], "Meerut")


if __name__ == "__main__":
    unittest.main()
