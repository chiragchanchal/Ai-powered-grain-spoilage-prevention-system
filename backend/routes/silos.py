"""
Silo Management & Live Status Endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.database.cassandra_client import cassandra_connector
from backend.services.weather_service import weather_service
from backend.services.alert_service import alert_service
from backend.services.psychrometrics import calculate_dew_point, calculate_equilibrium_moisture_content
from backend.knowledge_graph.neo4j_client import neo4j_connector
from backend.config import settings

router = APIRouter(prefix="/api/silos", tags=["Silos"])


class SiloCreateRequest(BaseModel):
    silo_id: str
    name: str
    grain_type: str = "wheat"
    capacity_tonnes: float = 500.0
    current_fill_tonnes: float = 400.0
    installed_sensors: str = "DHT22, CapMoisture, ThermalLance"
    region: str = "Haryana"
    lat: float = 28.4595
    lon: float = 77.0266


@router.get("", summary="List all silos with live risk state and telemetry")
def get_all_silos():
    silos = cassandra_connector.get_silos(settings.FACILITY_ID)
    weather = weather_service.get_weather(settings.DEFAULT_LAT, settings.DEFAULT_LON)
    results = []

    for s in silos:
        s_id = s["silo_id"]
        latest = cassandra_connector.get_latest_telemetry(s_id, settings.FACILITY_ID)
        if not latest:
            continue

        temp_c = float(latest["temp_c"])
        rh = float(latest["rel_humidity"])
        mc = float(latest["grain_moisture_pct"])
        risk_tier = latest.get("risk_tier", "LOW")
        p_risk = float(latest.get("p_risk", 0.1))

        # Rolling window for drift calculation
        window = cassandra_connector.get_rolling_window(s_id, settings.FACILITY_ID, limit=6)
        if len(window) >= 2:
            dt_dt = (temp_c - float(window[0]["temp_c"])) / max(1.0, len(window) - 1)
            drh_dt = (rh - float(window[0]["rel_humidity"])) / max(1.0, len(window) - 1)
        else:
            dt_dt = 0.0
            drh_dt = 0.0

        # Knowledge graph check
        kg_res = neo4j_connector.query_climate_risk(
            region_name=s["region"],
            grain_name=s["grain_type"],
            temp_c=temp_c,
            forecast_rh=weather["max_rh_48h"],
        )

        # Build playbook
        playbook = alert_service.generate_playbook(
            risk_tier=risk_tier,
            p_risk=p_risk,
            temp_c=temp_c,
            rh=rh,
            mc=mc,
            dt_dt=dt_dt,
            drh_dt=drh_dt,
            ext_temp_c=weather["current_temp_c"],
            ext_rh=weather["current_rh"],
            precip_prob=weather["precip_prob_48h"],
            kg_hazards=kg_res.get("matched_hazards", []),
            grain_type=s["grain_type"],
        )

        fill_percentage = round((s["current_fill_tonnes"] / max(s["capacity_tonnes"], 1.0)) * 100, 1)

        results.append({
            "silo_id": s_id,
            "name": s["name"],
            "grain_type": s["grain_type"],
            "capacity_tonnes": s["capacity_tonnes"],
            "current_fill_tonnes": s["current_fill_tonnes"],
            "fill_percentage": fill_percentage,
            "region": s["region"],
            "sensors": s["installed_sensors"],
            "telemetry": {
                "event_ts": latest["event_ts"],
                "temp_c": temp_c,
                "rel_humidity": rh,
                "grain_moisture_pct": mc,
                "dt_dt": round(dt_dt, 3),
                "drh_dt": round(drh_dt, 3),
                "dew_point_c": playbook["dew_point_c"],
                "emc_pct": playbook["equilibrium_moisture_pct"],
            },
            "risk_assessment": {
                "risk_tier": risk_tier,
                "p_risk": p_risk,
                "priority_level": playbook["priority_level"],
                "primary_command": playbook["primary_command"],
                "primary_command_hi": playbook["primary_command_hi"],
                "badge_color": playbook["badge_color"],
                "fan_action": playbook["fan_action"],
                "can_aerate": playbook["can_aerate"],
                "aeration_status": playbook["aeration_status"],
                "window_to_act": playbook["window_to_act"],
                "action_checklist": playbook["action_checklist"],
                "action_checklist_hi": playbook["action_checklist_hi"],
            },
            "climate_graph": {
                "kg_prior": kg_res.get("kg_risk_prior", 0.15),
                "matched_hazards": kg_res.get("matched_hazards", []),
                "active_paths": kg_res.get("active_paths", []),
            }
        })

    return {
        "facility_id": settings.FACILITY_ID,
        "facility_name": settings.FACILITY_NAME,
        "silos": results,
        "total_silos": len(results),
        "high_risk_count": sum(1 for r in results if r["risk_assessment"]["risk_tier"] == "HIGH"),
        "medium_risk_count": sum(1 for r in results if r["risk_assessment"]["risk_tier"] == "MEDIUM"),
        "low_risk_count": sum(1 for r in results if r["risk_assessment"]["risk_tier"] == "LOW"),
    }


@router.get("/{silo_id}", summary="Get detailed single silo view with historical telemetry")
def get_silo_detail(silo_id: str):
    silo = cassandra_connector.get_silo(silo_id, settings.FACILITY_ID)
    if not silo:
        raise HTTPException(status_code=404, detail="Silo not found")

    history = cassandra_connector.get_rolling_window(silo_id, settings.FACILITY_ID, limit=24)
    weather = weather_service.get_weather(settings.DEFAULT_LAT, settings.DEFAULT_LON)

    return {
        "silo": silo,
        "telemetry_history": history,
        "weather": weather,
    }
