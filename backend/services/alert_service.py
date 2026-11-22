"""
Preventive Action Playbook and Alert Generation Service.
Translates mathematical risk probabilities, psychrometric margins, and knowledge graph hazards
into clear, actionable, non-technical instructions for storage facility operators.
Includes Hindi (हिन्दी) translations for rural godown staff per Chapter 9 usability feedback.
"""

from typing import Dict, Any, List
from .psychrometrics import (
    calculate_dew_point,
    calculate_equilibrium_moisture_content,
    assess_aeration_feasibility,
    check_condensation_risk
)


class AlertService:
    @staticmethod
    def generate_playbook(
        risk_tier: str,
        p_risk: float,
        temp_c: float,
        rh: float,
        mc: float,
        dt_dt: float,
        drh_dt: float,
        ext_temp_c: float,
        ext_rh: float,
        precip_prob: float,
        kg_hazards: List[Dict[str, Any]] = None,
        grain_type: str = "wheat",
    ) -> Dict[str, Any]:
        """
        Synthesizes an operational playbook combining ML risk scoring and psychrometric ventilation rules.
        """
        kg_hazards = kg_hazards or []
        dew_point = calculate_dew_point(temp_c, rh)
        emc = calculate_equilibrium_moisture_content(temp_c, rh, grain_type)
        aeration = assess_aeration_feasibility(temp_c, rh, ext_temp_c, ext_rh, precip_prob)
        cond_risk, cond_msg = check_condensation_risk(temp_c, rh)

        action_checklist = []
        action_checklist_hi = []
        priority_level = "ROUTINE"
        window_to_act = "Maintain standard 48h check"
        primary_command = "Maintain routine storage monitoring"
        primary_command_hi = "नियमित भंडारण निगरानी बनाए रखें"

        # 1. Hotspot detection check (Thermal drift)
        is_hotspot = dt_dt >= 0.35  # > 0.35 C/hour sustained rise
        if is_hotspot:
            action_checklist.append("Thermal hotspot detected in grain core (heating rate +{:.2f}°C/hr). Insert portable probe into center stack and rotate top layer.".format(dt_dt))
            action_checklist_hi.append("अनाज के कोर में हॉटस्पॉट देखा गया (+{:.2f}°C/घंटा)। मध्य स्टैक में प्रोब डालें और ऊपरी परत को पलटें।".format(dt_dt))

        # 2. Aeration rule: Never open when outside humidity is high or rain forecast
        if not aeration["can_aerate"]:
            action_checklist.append(aeration["reason"])
            if "Rain" in aeration["reason"]:
                action_checklist_hi.append("बारिश का पूर्वानुमान है। सभी खिड़कियां, वेंटिलेशन और इनटेक तुरंत पूरी तरह बंद रखें।")
            else:
                action_checklist_hi.append(f"बाहरी आर्द्रता ({ext_rh:.1f}%) बहुत अधिक है। पंखे बंद रखें ताकि अनाज नमी न सोखे।")
        else:
            action_checklist.append(f"Ventilation window open: Outside air is drier ({ext_rh:.1f}% vs inside {rh:.1f}%). {aeration['reason']}")
            action_checklist_hi.append(f"हवा का अनुकूल समय: बाहर की हवा सूखी है ({ext_rh:.1f}%)। पंखे चलाकर अनाज को सुखाएं और ठंडा करें।")

        # 3. Moisture threshold check
        if mc > 14.5:
            action_checklist.append(f"Grain moisture ({mc:.1f}%) exceeds critical 14.5% storage threshold. Immediate batch turning or drying required.")
            action_checklist_hi.append(f"अनाज की नमी ({mc:.1f}%) सुरक्षित सीमा (14%) से अधिक है। तुरंत बैच को धूप में सुखाएं या टर्न करें।")
        elif mc > 13.5:
            action_checklist.append(f"Grain moisture ({mc:.1f}%) is elevated. Prioritize cool-night aeration.")
            action_checklist_hi.append(f"अनाज की नमी ({mc:.1f}%) बढ़ रही है। रात के ठंडे समय में पंखे चलाएं।")

        # 4. Condensation warning
        if cond_risk:
            action_checklist.append(cond_msg)
            action_checklist_hi.append("छत पर ओस/पसीना जमने का खतरा। छत के एग्जॉस्ट पंखे चलाकर भाप बाहर निकालें।")

        # 5. Integrate Knowledge Graph hazard warnings
        for h in kg_hazards[:2]:
            haz_name = h.get("hazard", "")
            action = h.get("action", "")
            if action:
                action_checklist.append(f"Pathogen Alert ({haz_name}): {action}")

        # Assemble summary by risk tier
        if risk_tier == "HIGH":
            priority_level = "IMMEDIATE_ACTION"
            window_to_act = "Execute within 4–6 hours"
            primary_command = "HIGH RISK ALERT: Immediate aeration or batch rotation required"
            primary_command_hi = "उच्च जोखिम चेतावनी: तुरंत पंखे चलाएं या अनाज के स्टैक को पलटें"
            badge_color = "#EF4444"  # Red
        elif risk_tier == "MEDIUM":
            priority_level = "PREVENTIVE_WARNING"
            window_to_act = "Schedule within 12–24 hours"
            primary_command = "MODERATE RISK: Microclimate drifting; schedule aeration during dry hours"
            primary_command_hi = "मध्यम जोखिम: नमी बढ़ रही है; सूखे समय में वेंटिलेशन शेड्यूल करें"
            badge_color = "#F59E0B"  # Amber
        else:
            priority_level = "SAFE_NORMAL"
            window_to_act = "Routine inspection within 48 hours"
            primary_command = "OPTIMAL STORAGE: Grain microclimate is stable within safe FAO limits"
            primary_command_hi = "सुरक्षित स्थिति: अनाज का तापमान और नमी सुरक्षित सीमा में है"
            badge_color = "#10B981"  # Green

        return {
            "risk_tier": risk_tier,
            "p_risk": round(p_risk, 3),
            "priority_level": priority_level,
            "window_to_act": window_to_act,
            "badge_color": badge_color,
            "primary_command": primary_command,
            "primary_command_hi": primary_command_hi,
            "fan_action": aeration["fan_action"],
            "can_aerate": aeration["can_aerate"],
            "aeration_status": aeration["status"],
            "aeration_reason": aeration["reason"],
            "dew_point_c": dew_point,
            "equilibrium_moisture_pct": emc,
            "condensation_alert": cond_risk,
            "condensation_detail": cond_msg,
            "action_checklist": action_checklist,
            "action_checklist_hi": action_checklist_hi,
        }


alert_service = AlertService()
