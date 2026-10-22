"""Unit tests for scheme eligibility engine."""

import unittest
from src.schemes.eligibility_engine import SchemeEligibilityEngine


class TestSchemes(unittest.TestCase):
    def setUp(self):
        self.engine = SchemeEligibilityEngine()

    def test_marginal_farmer_schemes(self):
        profile = {
            "plot_acres": 1.5,
            "crop": "Wheat",
            "state": "Uttar Pradesh",
            "irrigation_source": "Tube well / Borewell",
        }

        results = self.engine.evaluate_eligibility(profile)
        scheme_ids = [s["id"] for s in results]

        self.assertIn("pm-kisan", scheme_ids)
        self.assertIn("pmfby", scheme_ids)
        self.assertIn("soil-health-card", scheme_ids)
        self.assertIn("kcc", scheme_ids)

    def test_farmer_category_classification(self):
        self.assertEqual(self.engine.classify_farmer_category(0.8), "Marginal")
        self.assertEqual(self.engine.classify_farmer_category(3.0), "Small")
        self.assertEqual(self.engine.classify_farmer_category(6.0), "Medium")
        self.assertEqual(self.engine.classify_farmer_category(12.0), "Large")


if __name__ == "__main__":
    unittest.main()
