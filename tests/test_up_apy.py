"""Unit tests for official UP District APY processor and model pipeline."""

import unittest
from pathlib import Path
import pandas as pd
import joblib

from config.settings import PROCESSED_DATA_DIR, MODELS_DIR
from src.data_pipeline.up_apy_processor import process_up_apy_raw_data


class TestUpApyPipeline(unittest.TestCase):
    def test_processor_creates_tidy_dataset(self):
        df = process_up_apy_raw_data()
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 825)  # 75 districts x 11 years
        self.assertIn("yield_tonne_per_hectare", df.columns)
        self.assertIn("yield_quintals_per_acre", df.columns)
        self.assertIn("yield_lag_1", df.columns)
        self.assertEqual(df["district"].nunique(), 75)

    def test_trained_model_exists_and_predicts(self):
        model_path = MODELS_DIR / "best_up_district_apy_model.joblib"
        self.assertTrue(model_path.exists())
        pipeline = joblib.load(model_path)

        sample = pd.DataFrame(
            [
                {
                    "area_hectares": 250000.0,
                    "yield_lag_1": 3.2,
                    "yield_lag_2": 3.1,
                    "yield_rolling_3yr": 3.15,
                    "area_pct_change": 0.02,
                    "district": "Meerut",
                }
            ]
        )

        pred = pipeline.predict(sample)
        self.assertEqual(len(pred), 1)
        self.assertTrue(2.0 <= pred[0] <= 4.5)  # Realistic UP yield range


if __name__ == "__main__":
    unittest.main()
