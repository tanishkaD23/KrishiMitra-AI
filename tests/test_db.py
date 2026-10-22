"""Unit tests for SQLite database layer."""

import unittest
from src.database.db import (
    init_db,
    get_farmer_profile,
    get_farmer_plots,
    add_farmer_plot,
    get_historical_yields,
    log_prediction,
    get_model_benchmarks
)


class TestDatabaseLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_farmer_profile_exists(self):
        farmer = get_farmer_profile("farmer-001")
        self.assertIsNotNone(farmer)
        self.assertEqual(farmer["name"], "Tanishka")
        self.assertEqual(farmer["district"], "Meerut")
        self.assertGreaterEqual(farmer["plot_count"], 3)
        self.assertGreaterEqual(farmer["total_acres"], 4.5)

    def test_farmer_plots_retrieval(self):
        plots = get_farmer_plots("farmer-001")
        self.assertIsInstance(plots, list)
        self.assertGreaterEqual(len(plots), 3)
        crops = [p["crop"] for p in plots]
        self.assertIn("Wheat", crops)
        self.assertIn("Mustard", crops)

    def test_add_farmer_plot(self):
        new_plot = add_farmer_plot({
            "farmer_id": "farmer-001",
            "name": "Test Test Plot",
            "crop": "Wheat",
            "acres": 1.5,
            "village": "Modipuram",
            "district": "Meerut",
            "state": "Uttar Pradesh"
        })
        self.assertIsNotNone(new_plot)
        self.assertEqual(new_plot["name"], "Test Test Plot")
        self.assertEqual(new_plot["acres"], 1.5)

    def test_historical_yields_query(self):
        records = get_historical_yields("Meerut", "Wheat")
        self.assertIsInstance(records, list)
        self.assertGreater(len(records), 0)
        first = records[0]
        self.assertIn("yield_tonne_per_ha", first)
        self.assertIn("yield_quintals_per_acre", first)
        self.assertGreater(first["yield_tonne_per_ha"], 2.0)

    def test_model_benchmarks(self):
        benchmarks = get_model_benchmarks()
        self.assertIsInstance(benchmarks, list)
        self.assertGreaterEqual(len(benchmarks), 4)
        names = [b["model_name"] for b in benchmarks]
        self.assertIn("Previous-Year Baseline", names)

    def test_prediction_logging(self):
        # Should not raise exception
        log_prediction(
            crop="Wheat",
            district="Meerut",
            plot_acres=2.5,
            pred_q_acre=19.96,
            pred_q_ha=49.32,
            pred_t_ha=4.93,
            ci_lower=17.5,
            ci_upper=22.4,
            model_name="XGBoost Regressor (Pipeline)"
        )


if __name__ == "__main__":
    unittest.main()
