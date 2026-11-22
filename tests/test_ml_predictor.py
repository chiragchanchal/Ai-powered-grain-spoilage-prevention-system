"""
Unit Tests for Machine Learning Dual-Ensemble Inference.
"""

import unittest
import numpy as np
from ml_engine.predictor import predictor


class TestMLPredictor(unittest.TestCase):
    def test_safe_storage_prediction(self):
        # Temp 20°C, RH 50%, MC 12.0%, 0 drift, normal weather, low KG
        features = np.array([[20.0, 50.0, 12.0, 0.0, 0.0, 24.0, 55.0, 0.05, 0.10]], dtype=np.float32)
        res = predictor.predict(features, grain_type="wheat")
        self.assertEqual(res["risk_tier"], "LOW")
        self.assertLess(res["p_high"], 0.35)

    def test_critical_hotspot_prediction(self):
        # Temp 36°C, RH 72%, MC 14.8%, High drift +0.80 C/hr, high KG
        features = np.array([[36.0, 72.0, 14.8, 0.80, 0.30, 34.0, 75.0, 0.40, 0.85]], dtype=np.float32)
        res = predictor.predict(features, grain_type="wheat")
        self.assertEqual(res["risk_tier"], "HIGH")
        self.assertGreater(res["p_high"], 0.65)

    def test_safety_override_high_moisture(self):
        # Even if base probabilities are lower, MC > 14.5% triggers high-risk override
        features = np.array([[24.0, 60.0, 15.2, 0.0, 0.0, 26.0, 60.0, 0.10, 0.20]], dtype=np.float32)
        res = predictor.predict(features, grain_type="wheat")
        self.assertEqual(res["risk_tier"], "HIGH")
        self.assertIn("15.2", str(res["safety_override"]))


if __name__ == "__main__":
    unittest.main()
