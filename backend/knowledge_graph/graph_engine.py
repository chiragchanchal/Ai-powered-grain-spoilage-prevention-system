"""
In-Memory Climate-to-Spoilage Knowledge Graph Engine using NetworkX.
Implements domain-modeled graph traversal and Cypher-equivalent pattern matching
linking Regional climate events, crop susceptibility, spoilage pathogens, and operator interventions.
"""

import time
import networkx as nx
from typing import Dict, List, Any, Optional


class ClimateKnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl_seconds = 1800  # 30-minute TTL per Section 7.2 of report
        self._build_domain_graph()

    def _build_domain_graph(self):
        """Constructs the canonical CS002 Climate-Spoilage Knowledge Graph."""
        self.graph.clear()

        # 1. Regions
        regions = [
            ("reg_haryana", {"label": "Region", "name": "Haryana", "zone": "Trans-Gangetic Plains", "mandi_cluster": "Gurugram / Sohna / Karnal"}),
            ("reg_punjab", {"label": "Region", "name": "Punjab", "zone": "Trans-Gangetic Plains", "mandi_cluster": "Ludhiana / Khanna"}),
            ("reg_west_up", {"label": "Region", "name": "Western UP", "zone": "Upper Gangetic Plains", "mandi_cluster": "Meerut / Hapur"}),
        ]
        for node_id, attrs in regions:
            self.graph.add_node(node_id, **attrs)

        # 2. Climate Events
        climate_events = [
            ("clim_pre_monsoon", {
                "label": "ClimateEvent",
                "name": "Pre-Monsoon Humidity Surge",
                "min_temp": 26.0,
                "min_rh": 70.0,
                "historical_incidence_score": 0.88,
                "season": "June - July",
                "description": "Rapid moisture influx before heavy rainfall leads to interstitial humidity spikes.",
            }),
            ("clim_unseasonal_rain", {
                "label": "ClimateEvent",
                "name": "Unseasonal Post-Harvest Rainfall",
                "min_temp": 20.0,
                "min_rh": 75.0,
                "historical_incidence_score": 0.79,
                "season": "March - April / October",
                "description": "Western disturbances causing sudden dampening and wet grain intake.",
            }),
            ("clim_summer_heatwave", {
                "label": "ClimateEvent",
                "name": "Peak Summer Thermal Heatwave",
                "min_temp": 34.0,
                "min_rh": 35.0,
                "historical_incidence_score": 0.65,
                "season": "May - June",
                "description": "Elevated ambient heat accelerates insect metabolic reproduction and thermal convection.",
            }),
            ("clim_winter_fog", {
                "label": "ClimateEvent",
                "name": "Winter Fog & High Nighttime RH",
                "min_temp": 8.0,
                "min_rh": 80.0,
                "historical_incidence_score": 0.58,
                "season": "December - January",
                "description": "Severe temperature differential between grain core and cold roof causing condensation.",
            }),
        ]
        for node_id, attrs in climate_events:
            self.graph.add_node(node_id, **attrs)

        # 3. Spoilage Hazards
        spoilages = [
            ("spoil_aflatoxin", {
                "label": "SpoilageType",
                "name": "Aspergillus flavus (Aflatoxin B1)",
                "category": "Fungal Pathogen / Mycotoxin",
                "optimum_temp_min": 25.0,
                "optimum_temp_max": 37.0,
                "optimum_rh_min": 75.0,
                "danger_level": "CRITICAL",
                "recommended_action": "Immediate batch isolation; run high-capacity dry aeration if external RH < 60%; test aflatoxin ppb before sale.",
            }),
            ("spoil_penicillium", {
                "label": "SpoilageType",
                "name": "Penicillium Verrucosum Mold",
                "category": "Storage Mold",
                "optimum_temp_min": 18.0,
                "optimum_temp_max": 28.0,
                "optimum_rh_min": 72.0,
                "danger_level": "HIGH",
                "recommended_action": "Seal intake louvers against damp outside air; run recirculating dry air; inspect perimeter grain bags.",
            }),
            ("spoil_hotspot", {
                "label": "SpoilageType",
                "name": "Grain Self-Heating Hotspot",
                "category": "Biochemical Breakdown",
                "optimum_temp_min": 30.0,
                "optimum_temp_max": 55.0,
                "optimum_rh_min": 65.0,
                "danger_level": "HIGH",
                "recommended_action": "Core stack auger turning or physical aeration to break thermal core chimney; prevent caking.",
            }),
            ("spoil_weevil", {
                "label": "SpoilageType",
                "name": "Sitophilus oryzae (Rice Weevil)",
                "category": "Insect Infestation",
                "optimum_temp_min": 26.0,
                "optimum_temp_max": 34.0,
                "optimum_rh_min": 60.0,
                "danger_level": "MEDIUM",
                "recommended_action": "Cool grain mass below 18°C using nocturnal aeration cycles to inhibit oviposition.",
            }),
            ("spoil_condensation", {
                "label": "SpoilageType",
                "name": "Moisture Migration & Headspace Sweating",
                "category": "Physical Condensation",
                "optimum_temp_min": 8.0,
                "optimum_temp_max": 26.0,
                "optimum_rh_min": 80.0,
                "danger_level": "HIGH",
                "recommended_action": "Engage headspace roof exhaust fans to balance attic air temperature and evacuate vapor.",
            }),
        ]
        for node_id, attrs in spoilages:
            self.graph.add_node(node_id, **attrs)

        # 4. Grains
        grains = [
            ("grain_wheat", {"label": "GrainType", "name": "Wheat (HD-2967)", "family": "Cereal", "max_safe_mc": 13.5, "critical_mc": 14.5}),
            ("grain_paddy", {"label": "GrainType", "name": "Paddy (PB-1121)", "family": "Cereal", "max_safe_mc": 13.0, "critical_mc": 14.0}),
            ("grain_maize", {"label": "GrainType", "name": "Maize (Hybrid)", "family": "Cereal", "max_safe_mc": 13.5, "critical_mc": 14.5}),
        ]
        for node_id, attrs in grains:
            self.graph.add_node(node_id, **attrs)

        # 5. Edges: Region -> ClimateEvent
        for reg in ["reg_haryana", "reg_punjab", "reg_west_up"]:
            self.graph.add_edge(reg, "clim_pre_monsoon", relation="EXPERIENCES")
            self.graph.add_edge(reg, "clim_unseasonal_rain", relation="EXPERIENCES")
        self.graph.add_edge("reg_haryana", "clim_summer_heatwave", relation="EXPERIENCES")
        self.graph.add_edge("reg_haryana", "clim_winter_fog", relation="EXPERIENCES")
        self.graph.add_edge("reg_punjab", "clim_winter_fog", relation="EXPERIENCES")
        self.graph.add_edge("reg_west_up", "clim_summer_heatwave", relation="EXPERIENCES")

        # 6. Edges: ClimateEvent -> SpoilageType
        self.graph.add_edge("clim_pre_monsoon", "spoil_aflatoxin", relation="TRIGGERS", severity="HIGH", min_temp=26.0, min_rh=72.0, score=0.88)
        self.graph.add_edge("clim_pre_monsoon", "spoil_penicillium", relation="TRIGGERS", severity="HIGH", min_temp=24.0, min_rh=70.0, score=0.82)
        self.graph.add_edge("clim_pre_monsoon", "spoil_weevil", relation="TRIGGERS", severity="MEDIUM", min_temp=26.0, min_rh=65.0, score=0.74)

        self.graph.add_edge("clim_unseasonal_rain", "spoil_penicillium", relation="TRIGGERS", severity="HIGH", min_temp=20.0, min_rh=75.0, score=0.85)
        self.graph.add_edge("clim_unseasonal_rain", "spoil_condensation", relation="TRIGGERS", severity="HIGH", min_temp=22.0, min_rh=78.0, score=0.81)

        self.graph.add_edge("clim_summer_heatwave", "spoil_hotspot", relation="TRIGGERS", severity="HIGH", min_temp=34.0, min_rh=45.0, score=0.80)
        self.graph.add_edge("clim_summer_heatwave", "spoil_weevil", relation="TRIGGERS", severity="HIGH", min_temp=29.0, min_rh=55.0, score=0.78)

        self.graph.add_edge("clim_winter_fog", "spoil_condensation", relation="TRIGGERS", severity="HIGH", min_temp=8.0, min_rh=80.0, score=0.76)

        # 7. Edges: GrainType -> SpoilageType
        self.graph.add_edge("grain_wheat", "spoil_aflatoxin", relation="SUSCEPTIBLE_TO", vulnerability_weight=0.90)
        self.graph.add_edge("grain_wheat", "spoil_hotspot", relation="SUSCEPTIBLE_TO", vulnerability_weight=0.85)
        self.graph.add_edge("grain_wheat", "spoil_weevil", relation="SUSCEPTIBLE_TO", vulnerability_weight=0.82)

        self.graph.add_edge("grain_paddy", "spoil_aflatoxin", relation="SUSCEPTIBLE_TO", vulnerability_weight=0.92)
        self.graph.add_edge("grain_paddy", "spoil_penicillium", relation="SUSCEPTIBLE_TO", vulnerability_weight=0.88)
        self.graph.add_edge("grain_paddy", "spoil_condensation", relation="SUSCEPTIBLE_TO", vulnerability_weight=0.86)

        self.graph.add_edge("grain_maize", "spoil_aflatoxin", relation="SUSCEPTIBLE_TO", vulnerability_weight=0.95)
        self.graph.add_edge("grain_maize", "spoil_hotspot", relation="SUSCEPTIBLE_TO", vulnerability_weight=0.80)

    def query_climate_prior(
        self,
        region_name: str,
        grain_name: str,
        temp_c: float,
        forecast_rh: float,
    ) -> Dict[str, Any]:
        """
        Executes Cypher equivalent:
        MATCH (r:Region {name: $region})-[:EXPERIENCES]->(c:ClimateEvent)
              -[:TRIGGERS {severity: 'HIGH'}]->(s:SpoilageType)
              <-[:SUSCEPTIBLE_TO]-(g:GrainType {name: $grain_type})
        WHERE $forecast_rh >= c.min_rh AND $temp_c >= c.min_temp
        RETURN s.name AS hazard, avg(c.historical_incidence_score) AS kg_risk_prior,
               collect(DISTINCT s.recommended_action) AS preventive_actions;
        """
        cache_key = f"{region_name}_{grain_name}_{int(temp_c/2)}_{int(forecast_rh/5)}"
        now = time.time()
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["timestamp"] < self._cache_ttl_seconds:
                return entry["data"]

        # Find region node
        region_node = None
        for n, data in self.graph.nodes(data=True):
            if data.get("label") == "Region" and region_name.lower() in data.get("name", "").lower():
                region_node = n
                break
        if not region_node:
            region_node = "reg_haryana"

        # Find grain node
        grain_node = None
        for n, data in self.graph.nodes(data=True):
            if data.get("label") == "GrainType" and grain_name.lower() in data.get("name", "").lower():
                grain_node = n
                break
        if not grain_node:
            grain_node = "grain_wheat"

        # Traverse: (r)-[:EXPERIENCES]->(c)-[:TRIGGERS]->(s)<-[:SUSCEPTIBLE_TO]-(g)
        matched_hazards = []
        prior_scores = []
        preventive_actions = []
        active_paths = []

        # Find climate events experienced by region
        for _, clim_node, edge_data in self.graph.out_edges(region_node, data=True):
            if edge_data.get("relation") != "EXPERIENCES":
                continue
            clim_data = self.graph.nodes[clim_node]
            min_temp = clim_data.get("min_temp", 20.0)
            min_rh = clim_data.get("min_rh", 65.0)

            # Check weather thresholds
            if forecast_rh >= min_rh and temp_c >= min_temp:
                # Find triggered spoilages
                for _, spoil_node, trig_edge in self.graph.out_edges(clim_node, data=True):
                    if trig_edge.get("relation") != "TRIGGERS":
                        continue
                    # Check susceptibility from grain
                    if self.graph.has_edge(grain_node, spoil_node):
                        spoil_data = self.graph.nodes[spoil_node]
                        hazard_name = spoil_data.get("name")
                        score = trig_edge.get("score", 0.75)
                        action = spoil_data.get("recommended_action")

                        matched_hazards.append({
                            "hazard": hazard_name,
                            "category": spoil_data.get("category"),
                            "danger_level": spoil_data.get("danger_level"),
                            "score": score,
                            "action": action,
                            "triggering_event": clim_data.get("name"),
                        })
                        prior_scores.append(score)
                        if action and action not in preventive_actions:
                            preventive_actions.append(action)

                        active_paths.append({
                            "from": clim_data.get("name"),
                            "to": hazard_name,
                            "grain": self.graph.nodes[grain_node].get("name"),
                            "score": score,
                        })

        if prior_scores:
            kg_risk_prior = round(sum(prior_scores) / len(prior_scores), 3)
        else:
            # Baseline background prior when no active meteorological alert
            kg_risk_prior = 0.15

        result = {
            "kg_risk_prior": kg_risk_prior,
            "region": self.graph.nodes[region_node].get("name"),
            "grain": self.graph.nodes[grain_node].get("name"),
            "matched_hazards": matched_hazards,
            "preventive_actions": preventive_actions,
            "active_paths": active_paths,
            "has_climate_anomaly": len(matched_hazards) > 0,
        }

        self._cache[cache_key] = {"timestamp": now, "data": result}
        return result

    def get_full_graph_visualization(self) -> Dict[str, Any]:
        """Returns node and edge definitions formatted for frontend graph visualizers."""
        nodes = []
        for n, data in self.graph.nodes(data=True):
            nodes.append({
                "id": n,
                "label": data.get("label"),
                "name": data.get("name"),
                "category": data.get("category", ""),
                "description": data.get("description", ""),
            })

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation": data.get("relation"),
                "severity": data.get("severity", ""),
                "score": data.get("score", 0.0),
            })

        return {"nodes": nodes, "edges": edges}


# Global singleton instance
kg_instance = ClimateKnowledgeGraph()
