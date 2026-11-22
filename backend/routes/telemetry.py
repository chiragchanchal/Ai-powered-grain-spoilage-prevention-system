"""
Telemetry Ingestion and History Endpoints.
Accepts live IoT packets (e.g. from ESP32/LoRaWAN sensor nodes) or external gateways,
evaluates spoilage risk via dual ML ensemble, and stores into time-series persistence.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import datetime

from backend.database.cassandra_client import cassandra_connector
from backend.services.weather_service import weather_service
from backend.services.alert_service import alert_service
from backend.knowledge_graph.neo4j_client import neo4j_connector
from backend.config import settings
from ml_engine.predictor import predictor
from ml_engine.feature_pipeline import extract_features_from_window

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


class TelemetryIngestPacket(BaseModel):
    silo_id: str = Field(..., example="SILO_01")
    facility_id: str = Field(default=settings.FACILITY_ID)
    temp_c: float = Field(..., example=24.5)
    rel_humidity: float = Field(..., example=58.2)
    grain_moisture_pct: float = Field(..., example=12.9)
    event_ts: Optional[str] = None


@router.post("/ingest", summary="Ingest real-time IoT telemetry packet")
def ingest_telemetry(packet: TelemetryIngestPacket):
    silo = cassandra_connector.get_silo(packet.silo_id, packet.facility_id)
    if not silo:
        raise HTTPException(status_code=404, detail=f"Silo {packet.silo_id} not registered")

    ts = packet.event_ts or datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Fetch rolling window for drift rate calculation
    history = cassandra_connector.get_rolling_window(packet.silo_id, packet.facility_id, limit=5)
    history.append({
        "temp_c": packet.temp_c,
        "rel_humidity": packet.rel_humidity,
        "grain_moisture_pct": packet.grain_moisture_pct,
    })

    # 2. Fetch live weather context
    weather = weather_service.get_weather(silo.get("lat", settings.DEFAULT_LAT), silo.get("lon", settings.DEFAULT_LON))

    # 3. Query Knowledge Graph prior
    kg_res = neo4j_connector.query_climate_risk(
        region_name=silo.get("region", "Haryana"),
        grain_name=silo.get("grain_type", "wheat"),
        temp_c=packet.temp_c,
        forecast_rh=weather["max_rh_48h"],
    )

    # 4. Extract 9-feature vector & predict
    features = extract_features_from_window(history, weather, kg_res.get("kg_risk_prior", 0.15))
    pred = predictor.predict(features, grain_type=silo.get("grain_type", "wheat"))

    # 5. Generate preventive playbook
    playbook = alert_service.generate_playbook(
        risk_tier=pred["risk_tier"],
        p_risk=pred["p_high"],
        temp_c=packet.temp_c,
        rh=packet.rel_humidity,
        mc=packet.grain_moisture_pct,
        dt_dt=float(features[0][3]),
        drh_dt=float(features[0][4]),
        ext_temp_c=weather["current_temp_c"],
        ext_rh=weather["current_rh"],
        precip_prob=weather["precip_prob_48h"],
        kg_hazards=kg_res.get("matched_hazards", []),
        grain_type=silo.get("grain_type", "wheat"),
    )

    # 6. Store in Cassandra / Time-Series Database
    record = {
        "facility_id": packet.facility_id,
        "silo_id": packet.silo_id,
        "event_ts": ts,
        "date_bucket": ts[:7],
        "temp_c": packet.temp_c,
        "rel_humidity": packet.rel_humidity,
        "grain_moisture_pct": packet.grain_moisture_pct,
        "ext_temp_c": weather["current_temp_c"],
        "ext_humidity": weather["current_rh"],
        "precip_prob": weather["precip_prob_48h"],
        "risk_tier": pred["risk_tier"],
        "p_risk": pred["p_high"],
    }
    cassandra_connector.insert_telemetry(record)

    return {
        "status": "success",
        "ingested_timestamp": ts,
        "silo_id": packet.silo_id,
        "risk_tier": pred["risk_tier"],
        "p_high": pred["p_high"],
        "p_med": pred["p_med"],
        "p_low": pred["p_low"],
        "safety_override": pred["safety_override"],
        "contributing_factors": pred["contributing_factors"],
        "playbook": playbook,
    }


@router.get("/history/{silo_id}", summary="Get rolling window historical telemetry")
def get_telemetry_history(silo_id: str, limit: int = 24):
    history = cassandra_connector.get_rolling_window(silo_id, settings.FACILITY_ID, limit=limit)
    return {
        "silo_id": silo_id,
        "facility_id": settings.FACILITY_ID,
        "count": len(history),
        "history": history,
    }
