"""
Unit Tests for 9-Dimensional Feature Engineering Pipeline.
"""

import unittest
import numpy as np
from ml_engine.feature_pipeline import extract_features_from_window, extract_features_from_dict, FEATURE_NAMES


class TestFeaturePipeline(unittest.TestCase):
    def test_feature_names_length(self):
        self.assertEqual(len(FEATURE_NAMES), 9)

    def test_window_feature_extraction(self):
        telemetry_window = [
            {"temp_c": 22.0, "rel_humidity": 55.0, "grain_moisture_pct": 12.0},
            {"temp_c": 22.5, "rel_humidity": 56.0, "grain_moisture_pct": 12.1},
            {"temp_c": 23.0, "rel_humidity": 57.0, "grain_moisture_pct": 12.2},
        ]
        weather = {
            "max_temp_48h": 30.0,
            "max_rh_48h": 68.0,
            "precip_prob_48h": 0.20,
        }
        features = extract_features_from_window(telemetry_window, weather, kg_prior=0.25)
        self.assertEqual(features.shape, (1, 9))
        self.assertEqual(features[0][0], 23.0)  # latest temp
        self.assertEqual(features[0][1], 57.0)  # latest rh
        self.assertEqual(features[0][2], 12.2)  # latest mc
        self.assertAlmostEqual(features[0][3], 0.50, places=2)  # dt_dt: (23 - 22) / 2 = 0.50 C/hr
        self.assertEqual(features[0][8], 0.25)  # kg_prior

    def test_dict_feature_extraction(self):
        d = {
            "temp_c": 28.0,
            "rel_humidity": 72.0,
            "grain_moisture_pct": 14.6,
            "dt_dt": 0.35,
            "drh_dt": 0.40,
            "max_temp_48h": 34.0,
            "max_rh_48h": 80.0,
            "precip_prob_48h": 0.60,
            "kg_prior": 0.85,
        }
        features = extract_features_from_dict(d)
        self.assertEqual(features.shape, (1, 9))
        self.assertEqual(features[0][2], 14.6)


if __name__ == "__main__":
    unittest.main()
