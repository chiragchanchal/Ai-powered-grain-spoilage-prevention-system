"""
Climate Knowledge Graph API Endpoints.
Provides graph topology for frontend interactive visualizers and Cypher-equivalent queries.
"""

from fastapi import APIRouter
from backend.knowledge_graph.neo4j_client import neo4j_connector

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])


@router.get("/visualization", summary="Get nodes and edges for graph visualization")
def get_graph_visualization():
    return neo4j_connector.get_graph_visualization()


@router.get("/query", summary="Query climate hazard prior for region and grain type")
def query_graph_hazard(
    region: str = "Haryana",
    grain_type: str = "wheat",
    temp_c: float = 28.0,
    forecast_rh: float = 75.0,
):
    return neo4j_connector.query_climate_risk(
        region_name=region,
        grain_name=grain_type,
        temp_c=temp_c,
        forecast_rh=forecast_rh,
    )
