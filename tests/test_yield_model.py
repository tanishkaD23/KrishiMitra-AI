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

    def test_all_six_supported_states_predictions(self):
        """Test predictions across all 6 supported states (UP, MP, Bihar, Rajasthan, Punjab, Haryana)."""
        state_cases = [
            ("Uttar Pradesh", "Lucknow", "Wheat", 10.0, 26.0),
            ("Madhya Pradesh", "Bhopal", "Wheat", 9.0, 25.0),
            ("Bihar", "Patna", "Wheat", 8.0, 24.0),
            ("Rajasthan", "Jaipur", "Mustard", 4.0, 13.0),
            ("Punjab", "Ludhiana", "Wheat", 12.0, 26.0),
            ("Haryana", "Karnal", "Mustard", 4.5, 13.0),
        ]
        for state_name, district, crop, min_y, max_y in state_cases:
            res = self.predictor.predict({
                "state": state_name,
                "district": district,
                "crop": crop,
                "plot_acres": 2.5,
                "soil_type": "Alluvial (Sandy Loam)",
                "irrigation_source": "Tube well / Borewell",
                "sowing_window": "Timely Sown (Nov 01 - Nov 20)",
            })
            self.assertTrue(res["supported"], f"Failed for {state_name} ({district})")
            self.assertEqual(res["state"], state_name)
            self.assertEqual(res["district"], district)
            self.assertTrue(
                min_y <= res["predicted_yield_per_acre"] <= max_y,
                f"Yield {res['predicted_yield_per_acre']} out of range for {state_name}"
            )

    def test_missing_value_imputation_and_state_aliases(self):
        """Verify missing/None values and state abbreviations (e.g. MP, UP) are safely handled."""
        res = self.predictor.predict({
            "state": "MP",
            "district": "Indore",
            "crop": "Wheat",
            "plot_acres": None,
            "seasonal_rainfall_mm": None,
            "march_max_temp_c": float("nan"),
            "nitrogen_kg_acre": "",
        })
        self.assertTrue(res["supported"])
        self.assertEqual(res["state"], "Madhya Pradesh")
        self.assertEqual(res["plot_acres"], 2.0)
        self.assertGreater(res["predicted_yield_per_acre"], 8.0)


if __name__ == "__main__":
    unittest.main()
