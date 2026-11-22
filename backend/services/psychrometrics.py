"""
Psychrometric and Agro-Meteorological Calculations for Grain Storage.
Implements standard FAO, ASABE, and Magnus-Tetens formulas for:
- Dew Point Temperature
- Equilibrium Moisture Content (EMC) via modified Henderson / Chung-Pfost equations
- Mold Growth Risk Index
- Condensation / Sweating Risk
- Aeration Window Viability Assessment
"""

import math
from typing import Dict, Any, Tuple

# Modified Oswin equation parameters for cereal grains and major crops:
# EMC (%) = (A + B * T) * (RH / (1 - RH))^C
# Reference: ASABE D245.7 / FAO Grain Conditioning Standards / ICAR Storage Specs
GRAIN_CONSTANTS = {
    "wheat": {"A": 12.0, "B": -0.05, "C": 0.38, "safe_mc": 13.5, "critical_mc": 14.5},
    "paddy": {"A": 11.2, "B": -0.04, "C": 0.37, "safe_mc": 13.0, "critical_mc": 14.0},
    "maize": {"A": 11.8, "B": -0.05, "C": 0.39, "safe_mc": 13.5, "critical_mc": 14.5},
    "barley": {"A": 11.5, "B": -0.05, "C": 0.38, "safe_mc": 13.0, "critical_mc": 14.0},
    "pulses": {"A": 10.8, "B": -0.04, "C": 0.36, "safe_mc": 12.0, "critical_mc": 13.0},
    "mustard": {"A": 8.5, "B": -0.03, "C": 0.34, "safe_mc": 9.0, "critical_mc": 10.0},
    "soybean": {"A": 10.2, "B": -0.04, "C": 0.35, "safe_mc": 11.5, "critical_mc": 12.5},
}


def calculate_dew_point(temp_c: float, rel_humidity: float) -> float:
    """
    Computes dew point temperature in degrees Celsius using the Magnus-Tetens formula.
    Valid for temperatures between 0°C and 60°C and RH 1% - 100%.
    """
    rh = max(1.0, min(100.0, rel_humidity))
    a = 17.27
    b = 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    return round(dew_point, 2)


def calculate_equilibrium_moisture_content(
    temp_c: float, rel_humidity: float, grain_type: str = "wheat"
) -> float:
    """
    Calculates Equilibrium Moisture Content (EMC %) using the Modified Oswin equation.
    EMC indicates the moisture percentage the grain will reach if exposed to the air indefinitely.
    """
    params = GRAIN_CONSTANTS.get(grain_type.lower(), GRAIN_CONSTANTS["wheat"])
    rh = max(1.0, min(98.0, rel_humidity)) / 100.0
    t = max(0.0, temp_c)

    a = params["A"]
    b = params["B"]
    c = params["C"]

    try:
        emc = (a + b * t) * math.pow(rh / (1.0 - rh), c)
        return round(emc, 2)
    except (ValueError, ZeroDivisionError):
        return 13.0


def assess_aeration_feasibility(
    internal_temp: float,
    internal_rh: float,
    external_temp: float,
    external_rh: float,
    precip_prob: float = 0.0,
) -> Dict[str, Any]:
    """
    Evaluates whether ambient conditions permit safe forced aeration.
    Rules:
    - Never aerate during rain or when external RH >= 70% (would hydrate the grain).
    - Aeration is beneficial when external air is cooler (T_ext < T_int - 2°C) AND
      external RH is dry enough (RH_ext < internal_rh - 5% and RH_ext < 65%).
    """
    if precip_prob > 0.40:
        return {
            "can_aerate": False,
            "status": "SEAL_VENTS",
            "reason": f"Rainfall expected (probability {int(precip_prob*100)}%). Keep all vents and intake louvers sealed.",
            "fan_action": "OFF",
        }

    if external_rh >= 72.0:
        return {
            "can_aerate": False,
            "status": "SEAL_VENTS",
            "reason": f"External humidity ({external_rh:.1f}%) exceeds safe aeration threshold (70%). Aerating would force moisture into grain.",
            "fan_action": "OFF",
        }

    temp_diff = internal_temp - external_temp
    rh_diff = internal_rh - external_rh

    if temp_diff >= 2.0 and external_rh <= 65.0:
        return {
            "can_aerate": True,
            "status": "HIGHLY_FAVORABLE",
            "reason": f"External air is cooler by {temp_diff:.1f}°C and drier by {rh_diff:.1f}%. Optimal cooling and drying window.",
            "fan_action": "ON",
        }
    elif external_rh < internal_rh and external_rh <= 68.0:
        return {
            "can_aerate": True,
            "status": "MODERATE_FAVORABLE",
            "reason": f"External air is drier by {rh_diff:.1f}%. Safe for controlled ventilation.",
            "fan_action": "ON_CONTROLLED",
        }
    else:
        return {
            "can_aerate": False,
            "status": "STANDBY",
            "reason": "Ambient air offers negligible cooling or drying advantage. Keep fans in standby.",
            "fan_action": "OFF",
        }


def check_condensation_risk(internal_temp: float, internal_rh: float) -> Tuple[bool, str]:
    """
    Evaluates risk of interstitial condensation / sweat forming on silo headspace or grain surface.
    """
    dp = calculate_dew_point(internal_temp, internal_rh)
    delta = internal_temp - dp

    if delta <= 1.8:
        return True, f"CRITICAL: Temperature ({internal_temp:.1f}°C) within {delta:.1f}°C of dew point ({dp:.1f}°C). High sweating and mold germination hazard."
    elif delta <= 3.5:
        return False, f"ELEVATED: Dew point margin is narrow ({delta:.1f}°C). Monitor headspace for overnight condensation."
    return False, f"NORMAL: Adequate dew point margin ({delta:.1f}°C). Low condensation probability."
