"""
Stress Testing & Demonstration Simulation Engine.
Enables real-time injection of adverse pre-monsoon, hotspot, and condensation scenarios
for stakeholder demonstrations, academic evaluation, and operational training.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import datetime
from backend.database.cassandra_client import cassandra_connector
from backend.services.weather_service import weather_service
from backend.services.alert_service import alert_service
from backend.knowledge_graph.neo4j_client import neo4j_connector
from backend.config import settings
from ml_engine.predictor import predictor
from ml_engine.feature_pipeline import extract_features_from_window

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])

SCENARIOS = {
    "monsoon_spike": {
        "title": "Pre-Monsoon Humidity Surge & Imminent Rain",
        "description": "Simulates 78% external ambient humidity with 85% rain forecast, causing rapid interstitial moisture creep.",
        "silo_id": "SILO_02",
        "temp_c": 29.5,
        "rel_humidity": 74.0,
        "grain_moisture_pct": 14.2,
        "dt_dt": 0.15,
        "drh_dt": 0.55,
        "ext_temp_c": 31.0,
        "ext_humidity": 82.0,
        "precip_prob": 0.85,
    },
    "hotspot_heating": {
        "title": "Internal Grain Core Thermal Hotspot",
        "description": "Simulates rapid biological self-heating from localized mold/weevil respiration (+1.10°C/hr thermal drift).",
        "silo_id": "SILO_04",
        "temp_c": 38.5,
        "rel_humidity": 72.0,
        "grain_moisture_pct": 14.8,
        "dt_dt": 1.10,
        "drh_dt": 0.35,
        "ext_temp_c": 26.0,
        "ext_humidity": 55.0,
        "precip_prob": 0.10,
    },
    "moisture_leak": {
        "title": "Roof Leak / Over-Moisture Intake",
        "description": "Simulates excessive moisture influx exceeding 15.8% threshold, requiring emergency drying.",
        "silo_id": "SILO_01",
        "temp_c": 27.0,
        "rel_humidity": 84.0,
        "grain_moisture_pct": 15.9,
        "dt_dt": 0.20,
        "drh_dt": 0.80,
        "ext_temp_c": 27.5,
        "ext_humidity": 78.0,
        "precip_prob": 0.40,
    },
    "safe_winter": {
        "title": "Optimal Dry Winter Storage Condition",
        "description": "Simulates cool, dry, stabilized conditions within safe FAO equilibrium moisture boundaries.",
        "silo_id": "SILO_03",
        "temp_c": 19.5,
        "rel_humidity": 48.0,
        "grain_moisture_pct": 11.8,
        "dt_dt": -0.05,
        "drh_dt": -0.08,
        "ext_temp_c": 17.0,
        "ext_humidity": 45.0,
        "precip_prob": 0.05,
    },
}


class ScenarioTriggerRequest(BaseModel):
    scenario_key: str = Field(..., example="monsoon_spike")
    target_silo_id: str = Field(default=None)


@router.get("/scenarios", summary="List available demonstration stress scenarios")
def list_scenarios():
    return {
        "available_scenarios": [
            {
                "key": k,
                "title": v["title"],
                "description": v["description"],
                "target_silo": v["silo_id"],
            }
            for k, v in SCENARIOS.items()
        ]
    }


@router.post("/trigger", summary="Inject scenario telemetry into a silo and evaluate impact")
def trigger_scenario(req: ScenarioTriggerRequest):
    if req.scenario_key not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid scenario: {req.scenario_key}")

    scene = SCENARIOS[req.scenario_key]
    silo_id = req.target_silo_id or scene["silo_id"]
    silo = cassandra_connector.get_silo(silo_id, settings.FACILITY_ID)
    if not silo:
        # Graceful fallback: If the default demo silo was deleted or modified, use first available silo
        all_silos = cassandra_connector.get_silos(settings.FACILITY_ID)
        if all_silos:
            silo = all_silos[0]
            silo_id = silo["silo_id"]
        else:
            raise HTTPException(status_code=404, detail="No storage silos found in facility")

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Query Knowledge graph prior
    kg_res = neo4j_connector.query_climate_risk(
        region_name=silo.get("region", "Haryana"),
        grain_name=silo.get("grain_type", "wheat"),
        temp_c=scene["temp_c"],
        forecast_rh=scene["ext_humidity"],
    )

    # Ingest historical synthetic window to produce correct rate of change
    base_window = [
        {
            "temp_c": scene["temp_c"] - (scene["dt_dt"] * 2.0),
            "rel_humidity": scene["rel_humidity"] - (scene["drh_dt"] * 2.0),
            "grain_moisture_pct": scene["grain_moisture_pct"] - 0.2,
        },
        {
            "temp_c": scene["temp_c"] - scene["dt_dt"],
            "rel_humidity": scene["rel_humidity"] - scene["drh_dt"],
            "grain_moisture_pct": scene["grain_moisture_pct"] - 0.1,
        },
        {
            "temp_c": scene["temp_c"],
            "rel_humidity": scene["rel_humidity"],
            "grain_moisture_pct": scene["grain_moisture_pct"],
        }
    ]

    weather_mock = {
        "max_temp_48h": scene["ext_temp_c"],
        "max_rh_48h": scene["ext_humidity"],
        "precip_prob_48h": scene["precip_prob"],
        "current_temp_c": scene["ext_temp_c"],
        "current_rh": scene["ext_humidity"],
    }

    features = extract_features_from_window(base_window, weather_mock, kg_res.get("kg_risk_prior", 0.15))
    pred = predictor.predict(features, grain_type=silo.get("grain_type", "wheat"))

    playbook = alert_service.generate_playbook(
        risk_tier=pred["risk_tier"],
        p_risk=pred["p_high"],
        temp_c=scene["temp_c"],
        rh=scene["rel_humidity"],
        mc=scene["grain_moisture_pct"],
        dt_dt=scene["dt_dt"],
        drh_dt=scene["drh_dt"],
        ext_temp_c=scene["ext_temp_c"],
        ext_rh=scene["ext_humidity"],
        precip_prob=scene["precip_prob"],
        kg_hazards=kg_res.get("matched_hazards", []),
        grain_type=silo.get("grain_type", "wheat"),
    )

    # Persist injected telemetry into time-series store
    record = {
        "facility_id": settings.FACILITY_ID,
        "silo_id": silo_id,
        "event_ts": ts,
        "date_bucket": ts[:7],
        "temp_c": scene["temp_c"],
        "rel_humidity": scene["rel_humidity"],
        "grain_moisture_pct": scene["grain_moisture_pct"],
        "ext_temp_c": scene["ext_temp_c"],
        "ext_humidity": scene["ext_humidity"],
        "precip_prob": scene["precip_prob"],
        "risk_tier": pred["risk_tier"],
        "p_risk": pred["p_high"],
    }
    cassandra_connector.insert_telemetry(record)

    return {
        "scenario": scene["title"],
        "silo_id": silo_id,
        "injected_telemetry": record,
        "prediction": pred,
        "playbook": playbook,
    }


@router.post("/reset", summary="Reset all silos to standard safe baseline")
def reset_simulation():
    from backend.database.sqlite_timeseries import ts_store
    import os
    if os.path.exists(ts_store.db_path):
        os.remove(ts_store.db_path)
    ts_store._init_tables()
    ts_store._ensure_sample_data()
    return {"status": "success", "message": "All silos reset to verified baseline states."}
