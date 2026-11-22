"""
Unit Tests for Psychrometric and Agro-Meteorological Calculations.
"""

import unittest
from backend.services.psychrometrics import (
    calculate_dew_point,
    calculate_equilibrium_moisture_content,
    assess_aeration_feasibility,
    check_condensation_risk
)


class TestPsychrometrics(unittest.TestCase):
    def test_dew_point_calculation(self):
        # At 25°C and 50% RH, dew point is ~13.9°C
        dp = calculate_dew_point(25.0, 50.0)
        self.assertAlmostEqual(dp, 13.9, delta=0.5)

        # At 30°C and 80% RH, dew point is ~26.2°C
        dp_humid = calculate_dew_point(30.0, 80.0)
        self.assertAlmostEqual(dp_humid, 26.2, delta=0.5)

    def test_equilibrium_moisture_content(self):
        # At 25°C and 60% RH, wheat EMC should be in safe range (~12.5% to 13.5%)
        emc = calculate_equilibrium_moisture_content(25.0, 60.0, "wheat")
        self.assertTrue(11.5 <= emc <= 14.0, f"Observed EMC: {emc}")

    def test_aeration_feasibility_during_rain(self):
        # Rain probability high -> MUST seal vents
        decision = assess_aeration_feasibility(
            internal_temp=26.0,
            internal_rh=65.0,
            external_temp=22.0,
            external_rh=85.0,
            precip_prob=0.80,
        )
        self.assertFalse(decision["can_aerate"])
        self.assertEqual(decision["status"], "SEAL_VENTS")
        self.assertEqual(decision["fan_action"], "OFF")

    def test_aeration_feasibility_optimal_cool_dry(self):
        # Cool and dry outside -> Safe to ventilate
        decision = assess_aeration_feasibility(
            internal_temp=28.0,
            internal_rh=68.0,
            external_temp=20.0,
            external_rh=50.0,
            precip_prob=0.05,
        )
        self.assertTrue(decision["can_aerate"])
        self.assertEqual(decision["status"], "HIGHLY_FAVORABLE")
        self.assertEqual(decision["fan_action"], "ON")


if __name__ == "__main__":
    unittest.main()
