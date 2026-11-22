"""
Machine Learning Spoilage Prediction Endpoints.
Allows standalone inference with custom parameters for stress-testing and what-if analysis.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from ml_engine.predictor import predictor
from ml_engine.feature_pipeline import extract_features_from_dict
from backend.services.alert_service import alert_service
from backend.knowledge_graph.neo4j_client import neo4j_connector

router = APIRouter(prefix="/api/predict", tags=["Prediction"])


class PredictionRequest(BaseModel):
    grain_type: str = Field(default="wheat", example="wheat")
    region: str = Field(default="Haryana", example="Haryana")
    temp_c: float = Field(..., example=28.5)
    rel_humidity: float = Field(..., example=69.0)
    grain_moisture_pct: float = Field(..., example=14.2)
    dt_dt: float = Field(default=0.0, example=0.25)
    drh_dt: float = Field(default=0.0, example=0.15)
    max_temp_48h: float = Field(default=32.0, example=32.0)
    max_rh_48h: float = Field(default=75.0, example=75.0)
    precip_prob_48h: float = Field(default=0.45, example=0.45)
    kg_prior: Optional[float] = None


@router.post("", summary="Run dual-ensemble ML inference with custom inputs")
def predict_spoilage_risk(req: PredictionRequest):
    # 1. Determine KG prior if not explicitly provided
    if req.kg_prior is None:
        kg_res = neo4j_connector.query_climate_risk(
            region_name=req.region,
            grain_name=req.grain_type,
            temp_c=req.temp_c,
            forecast_rh=req.max_rh_48h,
        )
        kg_prior = kg_res.get("kg_risk_prior", 0.15)
        kg_hazards = kg_res.get("matched_hazards", [])
    else:
        kg_prior = req.kg_prior
        kg_hazards = []

    # 2. Extract features
    param_dict = {
        "temp_c": req.temp_c,
        "rh": req.rel_humidity,
        "mc": req.grain_moisture_pct,
        "dt_dt": req.dt_dt,
        "drh_dt": req.drh_dt,
        "max_temp_48h": req.max_temp_48h,
        "max_rh_48h": req.max_rh_48h,
        "precip_prob_48h": req.precip_prob_48h,
        "kg_prior": kg_prior,
    }
    features = extract_features_from_dict(param_dict)

    # 3. Dual-model inference
    pred = predictor.predict(features, grain_type=req.grain_type)

    # 4. Playbook synthesis
    playbook = alert_service.generate_playbook(
        risk_tier=pred["risk_tier"],
        p_risk=pred["p_high"],
        temp_c=req.temp_c,
        rh=req.rel_humidity,
        mc=req.grain_moisture_pct,
        dt_dt=req.dt_dt,
        drh_dt=req.drh_dt,
        ext_temp_c=req.max_temp_48h - 3.0,
        ext_rh=req.max_rh_48h,
        precip_prob=req.precip_prob_48h,
        kg_hazards=kg_hazards,
        grain_type=req.grain_type,
    )

    return {
        "inputs": param_dict,
        "prediction": pred,
        "playbook": playbook,
    }
