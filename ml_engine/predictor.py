"""
Dual-Model Ensemble Spoilage Predictor.
Fuses Random Forest tabular boundaries with Deep Neural Network probability distributions.
Implements the high-recall inference and safety override rules specified in Chapter 7.
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, List, Tuple
from .feature_pipeline import extract_features_from_window, extract_features_from_dict, FEATURE_NAMES

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
RF_PATH = os.path.join(MODEL_DIR, "rf_spoilage_model.joblib")
NN_PATH = os.path.join(MODEL_DIR, "nn_spoilage_model.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")


class SpoilagePredictor:
    def __init__(self):
        self.rf_model = None
        self.nn_model = None
        self.scaler = None
        self._load_models()

    def _load_models(self):
        if os.path.exists(RF_PATH) and os.path.exists(NN_PATH) and os.path.exists(SCALER_PATH):
            try:
                self.rf_model = joblib.load(RF_PATH)
                self.nn_model = joblib.load(NN_PATH)
                self.scaler = joblib.load(SCALER_PATH)
            except Exception as e:
                print(f"Error loading models: {e}. Re-running training...")
                from .train_models import train_and_evaluate_models
                train_and_evaluate_models()
                self.rf_model = joblib.load(RF_PATH)
                self.nn_model = joblib.load(NN_PATH)
                self.scaler = joblib.load(SCALER_PATH)
        else:
            from .train_models import train_and_evaluate_models
            train_and_evaluate_models()
            self.rf_model = joblib.load(RF_PATH)
            self.nn_model = joblib.load(NN_PATH)
            self.scaler = joblib.load(SCALER_PATH)

    def predict(
        self,
        features: np.ndarray,
        grain_type: str = "wheat",
    ) -> Dict[str, Any]:
        """
        Runs dual-model inference on 9-dimensional feature vector.
        Features format: [[temp_c, rh, mc, dt_dt, drh_dt, max_temp_48h, max_rh_48h, precip_prob_48h, kg_prior]]
        """
        temp_c = float(features[0][0])
        rh = float(features[0][1])
        mc = float(features[0][2])
        dt_dt = float(features[0][3])
        drh_dt = float(features[0][4])
        kg_prior = float(features[0][8])

        # 1. Random Forest Probabilities [Low, Med, High]
        p_rf = self.rf_model.predict_proba(features)[0]

        # 2. Neural Network Probabilities
        features_scaled = self.scaler.transform(features)
        p_nn = self.nn_model.predict_proba(features_scaled)[0]

        # 3. Weighted Ensemble (55% Random Forest, 45% Neural Network)
        p_combined = 0.55 * p_rf + 0.45 * p_nn

        p_low = float(p_combined[0])
        p_med = float(p_combined[1])
        p_high = float(p_combined[2])

        # 4. High-Recall Safety Overrides per CS002 Chapter 7 Specification
        # In grain storage, a false negative (failing to detect High Risk) causes entire silo spoilage!
        risk_tier = "LOW"
        override_triggered = None

        if p_high >= 0.70 or mc > 14.5 or (rh >= 68.0 and temp_c >= 28.0) or dt_dt >= 0.45:
            risk_tier = "HIGH"
            if mc > 14.5:
                override_triggered = f"Grain moisture ({mc:.1f}%) exceeds critical threshold (>14.5%)"
            elif rh >= 68.0 and temp_c >= 28.0:
                override_triggered = f"Psychrometric mold envelope active (RH {rh:.1f}% >= 68% and Temp {temp_c:.1f}°C >= 28°C)"
            elif dt_dt >= 0.45:
                override_triggered = f"Accelerating thermal core hotspot (Heating rate +{dt_dt:.2f}°C/hr)"
        elif p_combined[1] >= 0.35 or p_high >= 0.30 or mc > 13.0 or rh >= 62.0 or dt_dt >= 0.20:
            risk_tier = "MEDIUM"
            if mc > 13.0:
                override_triggered = f"Grain moisture ({mc:.1f}%) is in warning zone (>13.0%)"
            elif rh >= 62.0:
                override_triggered = f"Interstitial relative humidity ({rh:.1f}%) exceeds baseline (>62%)"
            elif dt_dt >= 0.20:
                override_triggered = f"Thermal drift (+{dt_dt:.2f}°C/hr)"
        else:
            risk_tier = "LOW"

        # Risk breakdown factors
        contributing_factors = []
        if mc > 13.5:
            contributing_factors.append({"factor": "Grain Moisture", "value": f"{mc:.1f}%", "severity": "HIGH" if mc > 14.5 else "MEDIUM"})
        if rh > 62.0:
            contributing_factors.append({"factor": "Relative Humidity", "value": f"{rh:.1f}%", "severity": "HIGH" if rh > 70.0 else "MEDIUM"})
        if dt_dt >= 0.20:
            contributing_factors.append({"factor": "Thermal Rise Rate", "value": f"+{dt_dt:.2f}°C/hr", "severity": "HIGH" if dt_dt >= 0.40 else "MEDIUM"})
        if kg_prior > 0.50:
            contributing_factors.append({"factor": "Climate Hazard Prior", "value": f"{kg_prior:.2f}", "severity": "HIGH" if kg_prior > 0.75 else "MEDIUM"})

        return {
            "risk_tier": risk_tier,
            "p_high": round(p_high, 4),
            "p_med": round(p_med, 4),
            "p_low": round(p_low, 4),
            "rf_probabilities": {"low": round(float(p_rf[0]), 4), "med": round(float(p_rf[1]), 4), "high": round(float(p_rf[2]), 4)},
            "nn_probabilities": {"low": round(float(p_nn[0]), 4), "med": round(float(p_nn[1]), 4), "high": round(float(p_nn[2]), 4)},
            "safety_override": override_triggered,
            "contributing_factors": contributing_factors,
        }


predictor = SpoilagePredictor()
