"""
Unit Tests for Climate Knowledge Graph Engine.
"""

import unittest
from backend.knowledge_graph.graph_engine import kg_instance


class TestKnowledgeGraph(unittest.TestCase):
    def test_graph_has_nodes_and_edges(self):
        viz = kg_instance.get_full_graph_visualization()
        self.assertGreater(len(viz["nodes"]), 10)
        self.assertGreater(len(viz["edges"]), 10)

    def test_query_climate_prior_anomaly(self):
        # In Haryana, with temp 28°C and forecast RH 76%, it should trigger Pre-Monsoon humidity surge
        res = kg_instance.query_climate_prior("Haryana", "Wheat (HD-2967)", temp_c=28.0, forecast_rh=76.0)
        self.assertTrue(res["has_climate_anomaly"])
        self.assertGreater(res["kg_risk_prior"], 0.70)
        self.assertGreater(len(res["matched_hazards"]), 0)
        # Verify aflatoxin or penicillium is matched
        hazards = [h["hazard"] for h in res["matched_hazards"]]
        self.assertTrue(any("Aspergillus" in h or "Penicillium" in h for h in hazards))

    def test_query_climate_prior_benign(self):
        # Cool, dry condition in winter
        res = kg_instance.query_climate_prior("Haryana", "Wheat (HD-2967)", temp_c=18.0, forecast_rh=45.0)
        self.assertFalse(res["has_climate_anomaly"])
        self.assertEqual(res["kg_risk_prior"], 0.15)


if __name__ == "__main__":
    unittest.main()
