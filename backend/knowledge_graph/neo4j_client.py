"""
Neo4j Client Interface with automatic Fallback to in-memory ClimateKnowledgeGraph.
Allows seamless plug-and-play operation with live Neo4j database or standalone in-memory execution.
"""

import os
import logging
from typing import Dict, Any
from .graph_engine import kg_instance

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class Neo4jConnector:
    def __init__(self):
        self.driver = None
        self.is_connected = False
        self._init_driver()

    def _init_driver(self):
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), max_connection_lifetime=30
            )
            # Quick connectivity check
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS connected")
                if result.single():
                    self.is_connected = True
                    logger.info("Connected successfully to external Neo4j instance at %s", NEO4J_URI)
        except Exception as e:
            self.is_connected = False
            logger.info("Neo4j external connection not active (%s). Operating with embedded high-performance graph engine.", e)

    def query_climate_risk(
        self,
        region_name: str,
        grain_name: str,
        temp_c: float,
        forecast_rh: float,
    ) -> Dict[str, Any]:
        """
        Executes query on live Neo4j if connected, else delegates to embedded graph engine.
        """
        if self.is_connected and self.driver:
            try:
                cypher_query = """
                MATCH (r:Region {name: $region})-[:EXPERIENCES]->(c:ClimateEvent)
                      -[:TRIGGERS {severity: 'HIGH'}]->(s:SpoilageType)
                      <-[:SUSCEPTIBLE_TO]-(g:GrainType {name: $grain_type})
                WHERE $forecast_rh >= c.min_rh AND $temp_c >= c.min_temp
                RETURN s.name AS hazard, avg(c.historical_incidence_score) AS kg_risk_prior,
                       collect(DISTINCT s.recommended_action) AS preventive_actions;
                """
                with self.driver.session() as session:
                    res = session.run(
                        cypher_query,
                        region=region_name,
                        grain_type=grain_name,
                        forecast_rh=forecast_rh,
                        temp_c=temp_c,
                    )
                    records = list(res)
                    if records:
                        priors = [r["kg_risk_prior"] for r in records if r["kg_risk_prior"] is not None]
                        actions = []
                        for r in records:
                            actions.extend(r["preventive_actions"] or [])
                        return {
                            "kg_risk_prior": round(sum(priors)/len(priors), 3) if priors else 0.15,
                            "region": region_name,
                            "grain": grain_name,
                            "matched_hazards": [{"hazard": r["hazard"]} for r in records],
                            "preventive_actions": list(set(actions)),
                            "active_paths": [],
                            "has_climate_anomaly": len(records) > 0,
                            "source": "Neo4j_Cluster",
                        }
            except Exception as ex:
                logger.warning("Neo4j query error: %s. Falling back to embedded graph.", ex)

        # Embedded graph engine
        res = kg_instance.query_climate_prior(region_name, grain_name, temp_c, forecast_rh)
        res["source"] = "Embedded_ClimateGraph_Engine"
        return res

    def get_graph_visualization(self) -> Dict[str, Any]:
        return kg_instance.get_full_graph_visualization()

    def close(self):
        if self.driver:
            self.driver.close()


neo4j_connector = Neo4jConnector()
