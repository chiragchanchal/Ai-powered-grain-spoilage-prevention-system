"""
Silo Management, Custom Telemetry Input & Farmer Customization Endpoints.
Enables farmers and godown operators to:
- Register custom storage silos & godowns
- Update capacity, fill level, and grain varieties (wheat, paddy, maize, pulses, mustard, etc.)
- Input manual moisture meter & temperature probe readings
- Customize farm / facility metadata
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import datetime

from backend.database.cassandra_client import cassandra_connector
from backend.services.weather_service import weather_service
from backend.services.alert_service import alert_service
from backend.services.psychrometrics import (
    calculate_dew_point,
    calculate_equilibrium_moisture_content,
    GRAIN_CONSTANTS
)
from backend.knowledge_graph.neo4j_client import neo4j_connector
from backend.config import settings
from ml_engine.predictor import predictor
from ml_engine.feature_pipeline import extract_features_from_window

router = APIRouter(prefix="/api/silos", tags=["Silos & Farmer Customization"])


class SiloCreateRequest(BaseModel):
    silo_id: Optional[str] = None
    name: str = Field(..., example="Kisan Godown Bin 1")
    grain_type: str = Field(default="wheat", example="wheat")
    capacity_tonnes: float = Field(default=200.0, example=200.0)
    current_fill_tonnes: float = Field(default=150.0, example=150.0)
    region: str = Field(default="Haryana", example="Haryana")
    initial_moisture_pct: Optional[float] = Field(default=12.8, example=12.8)
    initial_temp_c: Optional[float] = Field(default=24.0, example=24.0)
    initial_rh: Optional[float] = Field(default=58.0, example=58.0)


class SiloUpdateRequest(BaseModel):
    name: Optional[str] = None
    grain_type: Optional[str] = None
    capacity_tonnes: Optional[float] = None
    current_fill_tonnes: Optional[float] = None
    region: Optional[str] = None


class FarmerReadingRequest(BaseModel):
    grain_moisture_pct: float = Field(..., example=13.6, description="Grain moisture content % from hand meter")
    temp_c: float = Field(..., example=26.5, description="Stack internal temperature in °C")
    rel_humidity: Optional[float] = Field(default=60.0, example=60.0, description="Interstitial air relative humidity %")
    notes: Optional[str] = Field(default=None, example="Manual probe check before evening gate close")


class FacilityProfileRequest(BaseModel):
    name: str = Field(..., example="Sharma Agro Godown & Mandi Storage")
    region: str = Field(default="Haryana", example="Haryana")
    farmer_name: Optional[str] = Field(default="Ramesh Sharma", example="Ramesh Sharma")
    contact_phone: Optional[str] = Field(default="+91 98765 43210", example="+91 98765 43210")
    lat: Optional[float] = Field(default=28.4595, example=28.4595)
    lon: Optional[float] = Field(default=77.0266, example=77.0266)


@router.get("", summary="List all silos with live risk state and telemetry")
def get_all_silos():
    fac = cassandra_connector.get_facility(settings.FACILITY_ID)
    silos = cassandra_connector.get_silos(settings.FACILITY_ID)
    weather = weather_service.get_weather(fac.get("lat", settings.DEFAULT_LAT), fac.get("lon", settings.DEFAULT_LON))
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

        # Safe limit lookup
        grain_meta = GRAIN_CONSTANTS.get(s["grain_type"].lower(), GRAIN_CONSTANTS["wheat"])
        safe_mc_limit = grain_meta["critical_mc"]

        results.append({
            "silo_id": s_id,
            "name": s["name"],
            "grain_type": s["grain_type"],
            "capacity_tonnes": s["capacity_tonnes"],
            "current_fill_tonnes": s["current_fill_tonnes"],
            "fill_percentage": fill_percentage,
            "region": s["region"],
            "sensors": s["installed_sensors"],
            "safe_moisture_limit": safe_mc_limit,
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
        "facility_name": fac.get("name", settings.FACILITY_NAME),
        "farmer_name": fac.get("farmer_name", "Farmer In-Charge"),
        "contact_phone": fac.get("contact_phone", ""),
        "region": fac.get("region", settings.DEFAULT_REGION),
        "silos": results,
        "total_silos": len(results),
        "high_risk_count": sum(1 for r in results if r["risk_assessment"]["risk_tier"] == "HIGH"),
        "medium_risk_count": sum(1 for r in results if r["risk_assessment"]["risk_tier"] == "MEDIUM"),
        "low_risk_count": sum(1 for r in results if r["risk_assessment"]["risk_tier"] == "LOW"),
    }


@router.post("", summary="Add a custom storage silo / godown bin")
def create_custom_silo(req: SiloCreateRequest):
    fac = cassandra_connector.get_facility(settings.FACILITY_ID)
    silos = cassandra_connector.get_silos(settings.FACILITY_ID)

    # Auto-generate Silo ID if not provided
    silo_id = req.silo_id or f"SILO_{len(silos) + 1:02d}"

    silo_data = {
        "facility_id": settings.FACILITY_ID,
        "silo_id": silo_id,
        "name": req.name,
        "grain_type": req.grain_type.lower(),
        "capacity_tonnes": req.capacity_tonnes,
        "current_fill_tonnes": req.current_fill_tonnes,
        "installed_sensors": "Farmer Handheld Moisture Meter, Digital Probe",
        "region": req.region or fac.get("region", "Haryana"),
        "lat": fac.get("lat", settings.DEFAULT_LAT),
        "lon": fac.get("lon", settings.DEFAULT_LON),
    }
    cassandra_connector.add_silo(silo_data)

    # Initialize initial baseline telemetry reading
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    weather = weather_service.get_weather(fac.get("lat", settings.DEFAULT_LAT), fac.get("lon", settings.DEFAULT_LON))

    initial_mc = req.initial_moisture_pct or 12.8
    initial_temp = req.initial_temp_c or 24.0
    initial_rh = req.initial_rh or 58.0

    # Baseline risk check
    risk = "LOW"
    if initial_mc > 14.5 or (initial_rh >= 68.0 and initial_temp >= 28.0):
        risk = "HIGH"
    elif initial_mc > 13.0 or initial_rh >= 62.0:
        risk = "MEDIUM"

    cassandra_connector.insert_telemetry({
        "facility_id": settings.FACILITY_ID,
        "silo_id": silo_id,
        "event_ts": now,
        "date_bucket": now[:7],
        "temp_c": initial_temp,
        "rel_humidity": initial_rh,
        "grain_moisture_pct": initial_mc,
        "ext_temp_c": weather["current_temp_c"],
        "ext_humidity": weather["current_rh"],
        "precip_prob": weather["precip_prob_48h"],
        "risk_tier": risk,
        "p_risk": 0.15 if risk == "LOW" else (0.45 if risk == "MEDIUM" else 0.85),
    })

    return {
        "status": "success",
        "message": f"Storage unit '{req.name}' successfully registered.",
        "silo_id": silo_id,
    }


@router.put("/{silo_id}", summary="Update custom storage unit details")
def update_custom_silo(silo_id: str, req: SiloUpdateRequest):
    silo = cassandra_connector.get_silo(silo_id, settings.FACILITY_ID)
    if not silo:
        raise HTTPException(status_code=404, detail="Silo not found")

    update_dict = {k: v for k, v in req.model_dump().items() if v is not None}
    cassandra_connector.update_silo(silo_id, update_dict, settings.FACILITY_ID)
    return {"status": "success", "message": f"Silo {silo_id} updated successfully."}


@router.delete("/{silo_id}", summary="Delete a storage unit")
def delete_custom_silo(silo_id: str):
    silo = cassandra_connector.get_silo(silo_id, settings.FACILITY_ID)
    if not silo:
        raise HTTPException(status_code=404, detail="Silo not found")

    cassandra_connector.delete_silo(silo_id, settings.FACILITY_ID)
    return {"status": "success", "message": f"Silo {silo_id} deleted."}


@router.post("/{silo_id}/reading", summary="Farmer inputs custom manual moisture meter & temperature reading")
def input_farmer_reading(silo_id: str, reading: FarmerReadingRequest):
    silo = cassandra_connector.get_silo(silo_id, settings.FACILITY_ID)
    if not silo:
        raise HTTPException(status_code=404, detail="Silo not found")

    fac = cassandra_connector.get_facility(settings.FACILITY_ID)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Rolling window for drift calculation
    history = cassandra_connector.get_rolling_window(silo_id, settings.FACILITY_ID, limit=5)
    history.append({
        "temp_c": reading.temp_c,
        "rel_humidity": reading.rel_humidity,
        "grain_moisture_pct": reading.grain_moisture_pct,
    })

    # 2. Weather context
    weather = weather_service.get_weather(fac.get("lat", settings.DEFAULT_LAT), fac.get("lon", settings.DEFAULT_LON))

    # 3. Knowledge graph query
    kg_res = neo4j_connector.query_climate_risk(
        region_name=silo.get("region", fac.get("region", "Haryana")),
        grain_name=silo.get("grain_type", "wheat"),
        temp_c=reading.temp_c,
        forecast_rh=weather["max_rh_48h"],
    )

    # 4. Predict
    features = extract_features_from_window(history, weather, kg_res.get("kg_risk_prior", 0.15))
    pred = predictor.predict(features, grain_type=silo.get("grain_type", "wheat"))

    # 5. Playbook
    playbook = alert_service.generate_playbook(
        risk_tier=pred["risk_tier"],
        p_risk=pred["p_high"],
        temp_c=reading.temp_c,
        rh=reading.rel_humidity,
        mc=reading.grain_moisture_pct,
        dt_dt=float(features[0][3]),
        drh_dt=float(features[0][4]),
        ext_temp_c=weather["current_temp_c"],
        ext_rh=weather["current_rh"],
        precip_prob=weather["precip_prob_48h"],
        kg_hazards=kg_res.get("matched_hazards", []),
        grain_type=silo.get("grain_type", "wheat"),
    )

    # 6. Save in time-series
    record = {
        "facility_id": settings.FACILITY_ID,
        "silo_id": silo_id,
        "event_ts": now,
        "date_bucket": now[:7],
        "temp_c": reading.temp_c,
        "rel_humidity": reading.rel_humidity,
        "grain_moisture_pct": reading.grain_moisture_pct,
        "ext_temp_c": weather["current_temp_c"],
        "ext_humidity": weather["current_rh"],
        "precip_prob": weather["precip_prob_48h"],
        "risk_tier": pred["risk_tier"],
        "p_risk": pred["p_high"],
    }
    cassandra_connector.insert_telemetry(record)

    return {
        "status": "success",
        "message": f"Reading saved for {silo.get('name')}.",
        "silo_id": silo_id,
        "prediction": pred,
        "playbook": playbook,
        "recorded_telemetry": record,
    }


@router.get("/facility/profile", summary="Get custom farm or facility profile")
def get_facility_profile():
    return cassandra_connector.get_facility(settings.FACILITY_ID)


@router.put("/facility/profile", summary="Update custom farm or facility profile")
def update_facility_profile(req: FacilityProfileRequest):
    data = req.model_dump()
    data["facility_id"] = settings.FACILITY_ID
    cassandra_connector.update_facility(data)
    return {"status": "success", "message": "Farm profile updated successfully.", "profile": data}


@router.get("/{silo_id}", summary="Get detailed single silo view with historical telemetry")
def get_silo_detail(silo_id: str):
    silo = cassandra_connector.get_silo(silo_id, settings.FACILITY_ID)
    if not silo:
        raise HTTPException(status_code=404, detail="Silo not found")

    fac = cassandra_connector.get_facility(settings.FACILITY_ID)
    history = cassandra_connector.get_rolling_window(silo_id, settings.FACILITY_ID, limit=24)
    weather = weather_service.get_weather(fac.get("lat", settings.DEFAULT_LAT), fac.get("lon", settings.DEFAULT_LON))

    return {
        "silo": silo,
        "telemetry_history": history,
        "weather": weather,
    }
