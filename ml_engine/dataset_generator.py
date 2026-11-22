"""
Synthetic & Empirical Grain Storage Microclimate Dataset Generator.
Grounded in FAO Post-Harvest Manuals (Section 2.2.5), ICAR-CIPHET benchmarks,
and ASABE equilibrium moisture standards for North Indian grain storage facilities.
"""

import numpy as np
import pandas as pd
from typing import Tuple
from .feature_pipeline import FEATURE_NAMES


def generate_grain_spoilage_dataset(
    n_samples: int = 6000, random_seed: int = 42
) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Generates balanced multi-tier dataset:
    - 0: LOW RISK (Optimal safe storage)
    - 1: MEDIUM RISK (Elevated moisture / pre-monsoon drift)
    - 2: HIGH RISK (Critical mold / aflatoxin / thermal hotspot danger)
    """
    np.random.seed(random_seed)
    n_per_class = n_samples // 3

    # ==========================================
    # CLASS 0: LOW RISK (Safe Storage)
    # T in [16, 26]°C, RH in [40, 62]%, MC in [10.5, 13.2]%
    # Stable drift (-0.1 to +0.1), mild weather, low KG prior
    # ==========================================
    c0_temp = np.random.uniform(16.0, 26.5, n_per_class)
    c0_rh = np.random.uniform(40.0, 62.0, n_per_class)
    c0_mc = np.random.uniform(10.5, 13.2, n_per_class)
    c0_dt = np.random.normal(0.0, 0.05, n_per_class)
    c0_drh = np.random.normal(0.0, 0.10, n_per_class)
    c0_w_temp = c0_temp + np.random.uniform(-3.0, 5.0, n_per_class)
    c0_w_rh = np.random.uniform(35.0, 65.0, n_per_class)
    c0_w_pop = np.random.uniform(0.0, 0.25, n_per_class)
    c0_kg = np.random.uniform(0.05, 0.30, n_per_class)
    c0_labels = np.zeros(n_per_class, dtype=int)

    # ==========================================
    # CLASS 1: MEDIUM RISK (Elevated / Warning)
    # T in [24, 32]°C, RH in [62, 73]%, MC in [13.2, 14.4]%
    # Mild drift (+0.1 to +0.35 C/h), incoming weather drift, moderate KG prior
    # ==========================================
    c1_temp = np.random.uniform(24.0, 32.0, n_per_class)
    c1_rh = np.random.uniform(62.0, 73.0, n_per_class)
    c1_mc = np.random.uniform(13.2, 14.4, n_per_class)
    c1_dt = np.random.uniform(0.05, 0.30, n_per_class)
    c1_drh = np.random.uniform(0.10, 0.45, n_per_class)
    c1_w_temp = np.random.uniform(28.0, 36.0, n_per_class)
    c1_w_rh = np.random.uniform(65.0, 80.0, n_per_class)
    c1_w_pop = np.random.uniform(0.20, 0.60, n_per_class)
    c1_kg = np.random.uniform(0.35, 0.70, n_per_class)
    c1_labels = np.ones(n_per_class, dtype=int)

    # ==========================================
    # CLASS 2: HIGH RISK (Critical Hazard)
    # Subtype A: Pre-monsoon severe moisture surge (RH > 75%, MC > 14.5%)
    # Subtype B: Active thermal hotspot (dT/dt > 0.40°C/hr, T > 30°C)
    # Subtype C: Dangerous heat + moisture interaction
    # ==========================================
    half_c2 = n_per_class // 2
    # Subtype A (High Moisture / Fungal Bloom)
    c2_temp_a = np.random.uniform(27.0, 36.0, half_c2)
    c2_rh_a = np.random.uniform(74.0, 92.0, half_c2)
    c2_mc_a = np.random.uniform(14.5, 17.5, half_c2)
    c2_dt_a = np.random.uniform(0.10, 0.40, half_c2)
    c2_drh_a = np.random.uniform(0.30, 0.90, half_c2)
    c2_w_temp_a = np.random.uniform(30.0, 38.0, half_c2)
    c2_w_rh_a = np.random.uniform(75.0, 95.0, half_c2)
    c2_w_pop_a = np.random.uniform(0.50, 0.95, half_c2)
    c2_kg_a = np.random.uniform(0.70, 0.95, half_c2)

    # Subtype B (Biological Thermal Hotspot)
    other_half = n_per_class - half_c2
    c2_temp_b = np.random.uniform(31.0, 48.0, other_half)
    c2_rh_b = np.random.uniform(65.0, 85.0, other_half)
    c2_mc_b = np.random.uniform(13.8, 16.5, other_half)
    c2_dt_b = np.random.uniform(0.40, 1.40, other_half)  # Rapid hotspot rise
    c2_drh_b = np.random.uniform(0.20, 0.70, other_half)
    c2_w_temp_b = np.random.uniform(28.0, 38.0, other_half)
    c2_w_rh_b = np.random.uniform(60.0, 88.0, other_half)
    c2_w_pop_b = np.random.uniform(0.30, 0.85, other_half)
    c2_kg_b = np.random.uniform(0.65, 0.92, other_half)

    c2_temp = np.concatenate([c2_temp_a, c2_temp_b])
    c2_rh = np.concatenate([c2_rh_a, c2_rh_b])
    c2_mc = np.concatenate([c2_mc_a, c2_mc_b])
    c2_dt = np.concatenate([c2_dt_a, c2_dt_b])
    c2_drh = np.concatenate([c2_drh_a, c2_drh_b])
    c2_w_temp = np.concatenate([c2_w_temp_a, c2_w_temp_b])
    c2_w_rh = np.concatenate([c2_w_rh_a, c2_w_rh_b])
    c2_w_pop = np.concatenate([c2_w_pop_a, c2_w_pop_b])
    c2_kg = np.concatenate([c2_kg_a, c2_kg_b])
    c2_labels = np.full(n_per_class, 2, dtype=int)

    # Combine all classes
    X = np.column_stack([
        np.concatenate([c0_temp, c1_temp, c2_temp]),
        np.concatenate([c0_rh, c1_rh, c2_rh]),
        np.concatenate([c0_mc, c1_mc, c2_mc]),
        np.concatenate([c0_dt, c1_dt, c2_dt]),
        np.concatenate([c0_drh, c1_drh, c2_drh]),
        np.concatenate([c0_w_temp, c1_w_temp, c2_w_temp]),
        np.concatenate([c0_w_rh, c1_w_rh, c2_w_rh]),
        np.concatenate([c0_w_pop, c1_w_pop, c2_w_pop]),
        np.concatenate([c0_kg, c1_kg, c2_kg]),
    ])
    y = np.concatenate([c0_labels, c1_labels, c2_labels])

    # Shuffle dataset
    indices = np.random.permutation(len(y))
    X = X[indices]
    y = y[indices]

    df = pd.DataFrame(X, columns=FEATURE_NAMES)
    df["risk_tier"] = y

    return X, y, df
