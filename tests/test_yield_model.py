"""Unit tests for yield modeling and inference pipeline."""

import unittest
from src.yield_model.predict import YieldPredictor


class TestYieldModel(unittest.TestCase):
    def setUp(self):
        self.predictor = YieldPredictor()

    def test_wheat_prediction_range(self):
        farmer_input = {
            "crop": "Wheat",
            "district": "Meerut",
            "plot_acres": 2.0,
            "soil_type": "Alluvial (Sandy Loam)",
            "irrigation_source": "Tube well / Borewell",
            "sowing_window": "Timely Sown (Nov 01 - Nov 20)",
            "seasonal_rainfall_mm": 65.0,
            "march_max_temp_c": 31.0,
            "nitrogen_kg_acre": 50.0,
            "phosphorus_kg_acre": 22.0,
            "potassium_kg_acre": 15.0,
        }

        result = self.predictor.predict(farmer_input)

        self.assertEqual(result["crop"], "Wheat")
        self.assertEqual(result["plot_acres"], 2.0)
        self.assertTrue(10.0 <= result["predicted_yield_per_acre"] <= 26.0)
        self.assertEqual(
            result["total_harvest_quintals"],
            round(result["predicted_yield_per_acre"] * 2.0, 2),
        )
        self.assertLess(
            result["confidence_interval_90"]["lower"],
            result["predicted_yield_per_acre"],
        )
        self.assertGreater(
            result["confidence_interval_90"]["upper"],
            result["predicted_yield_per_acre"],
        )

    def test_mustard_prediction_range(self):
        farmer_input = {
            "crop": "Mustard",
            "district": "Bulandshahr",
            "plot_acres": 1.5,
            "soil_type": "Alluvial (Sandy Loam)",
            "irrigation_source": "Tube well / Borewell",
            "sowing_window": "Early Rabi (Oct 15 - Oct 31)",
            "seasonal_rainfall_mm": 50.0,
            "march_max_temp_c": 30.5,
            "nitrogen_kg_acre": 35.0,
            "phosphorus_kg_acre": 18.0,
            "potassium_kg_acre": 10.0,
        }

        result = self.predictor.predict(farmer_input)

        self.assertEqual(result["crop"], "Mustard")
        self.assertTrue(4.0 <= result["predicted_yield_per_acre"] <= 12.0)


if __name__ == "__main__":
    unittest.main()
