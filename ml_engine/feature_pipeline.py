"""
Feature Engineering Pipeline for AI Grain Spoilage Risk Engine.
Constructs 9-dimensional normalized feature vectors combining real-time silo telemetry,
thermal drift rates, 48-hour meteorological forecasts, and Neo4j knowledge graph priors.
"""

import numpy as np
from typing import List, Dict, Any, Tuple


FEATURE_NAMES = [
    "temp_c",
    "rh",
    "mc",
    "dt_dt",
    "drh_dt",
    "max_temp_48h",
    "max_rh_48h",
    "precip_prob_48h",
    "kg_prior",
]


def extract_features_from_window(
    telemetry_window: List[Dict[str, Any]],
    weather_forecast: Dict[str, Any],
    kg_prior: float = 0.15,
) -> np.ndarray:
    """
    Extracts 9-feature array from a rolling telemetry window and weather forecast.
    """
    if not telemetry_window:
        # Default fallback values
        return np.array([[24.0, 58.0, 12.8, 0.0, 0.0, 28.0, 65.0, 0.1, 0.15]], dtype=np.float32)

    latest = telemetry_window[-1]
    t_now = float(latest.get("temp_c", 24.0))
    rh_now = float(latest.get("rel_humidity", latest.get("rh", 58.0)))
    mc_now = float(latest.get("grain_moisture_pct", latest.get("mc", 12.8)))

    # Compute drift rates over window
    if len(telemetry_window) >= 2:
        earliest = telemetry_window[0]
        t_prev = float(earliest.get("temp_c", t_now))
        rh_prev = float(earliest.get("rel_humidity", earliest.get("rh", rh_now)))
        hours = max(1.0, float(len(telemetry_window) - 1))
        dt_dt = (t_now - t_prev) / hours
        drh_dt = (rh_now - rh_prev) / hours
    else:
        dt_dt = float(latest.get("dt_dt", 0.0))
        drh_dt = float(latest.get("drh_dt", 0.0))

    max_temp_48h = float(weather_forecast.get("max_temp_48h", 28.0))
    max_rh_48h = float(weather_forecast.get("max_rh_48h", 65.0))
    precip_prob_48h = float(weather_forecast.get("precip_prob_48h", 0.10))

    features = np.array([[
        t_now,
        rh_now,
        mc_now,
        round(dt_dt, 3),
        round(drh_dt, 3),
        max_temp_48h,
        max_rh_48h,
        precip_prob_48h,
        float(kg_prior),
    ]], dtype=np.float32)

    return features


def extract_features_from_dict(params: Dict[str, Any]) -> np.ndarray:
    """
    Direct extraction from single-point dictionary for testing / simulation.
    """
    features = np.array([[
        float(params.get("temp_c", 24.0)),
        float(params.get("rh", params.get("rel_humidity", 58.0))),
        float(params.get("mc", params.get("grain_moisture_pct", 12.8))),
        float(params.get("dt_dt", 0.0)),
        float(params.get("drh_dt", 0.0)),
        float(params.get("max_temp_48h", 28.0)),
        float(params.get("max_rh_48h", 65.0)),
        float(params.get("precip_prob_48h", 0.1)),
        float(params.get("kg_prior", 0.15)),
    ]], dtype=np.float32)

    return features
