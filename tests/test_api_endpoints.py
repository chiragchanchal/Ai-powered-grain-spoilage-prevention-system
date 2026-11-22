"""
Integration Tests for FastAPI Endpoints.
"""

import unittest
from fastapi.testclient import TestClient
from backend.main import app


class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")

    def test_get_all_silos(self):
        res = self.client.get("/api/silos")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("silos", data)
        self.assertGreaterEqual(len(data["silos"]), 1)

    def test_get_current_weather(self):
        res = self.client.get("/api/weather/current")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("current_temp_c", data)
        self.assertIn("max_rh_48h", data)

    def test_custom_prediction_endpoint(self):
        payload = {
            "grain_type": "wheat",
            "region": "Haryana",
            "temp_c": 32.0,
            "rel_humidity": 78.0,
            "grain_moisture_pct": 15.0,
            "dt_dt": 0.40,
            "drh_dt": 0.30,
            "max_temp_48h": 35.0,
            "max_rh_48h": 82.0,
            "precip_prob_48h": 0.70,
        }
        res = self.client.post("/api/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["prediction"]["risk_tier"], "HIGH")
        self.assertIn("playbook", data)

    def test_telemetry_ingest(self):
        packet = {
            "silo_id": "SILO_01",
            "facility_id": "FAC_GURUGRAM_01",
            "temp_c": 23.8,
            "rel_humidity": 58.5,
            "grain_moisture_pct": 12.7,
        }
        res = self.client.post("/api/telemetry/ingest", json=packet)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")

    def test_simulation_scenarios_and_trigger(self):
        # 1. List scenarios
        res_list = self.client.get("/api/simulation/scenarios")
        self.assertEqual(res_list.status_code, 200)
        scenarios = res_list.json()["available_scenarios"]
        self.assertGreaterEqual(len(scenarios), 3)

        # 2. Trigger hotspot scenario
        res_trig = self.client.post("/api/simulation/trigger", json={"scenario_key": "hotspot_heating"})
        self.assertEqual(res_trig.status_code, 200)
        data = res_trig.json()
        self.assertEqual(data["prediction"]["risk_tier"], "HIGH")

    def test_farmer_customization_lifecycle(self):
        # 1. Add custom silo
        new_silo = {
            "silo_id": "FARMER_BIN_99",
            "name": "Chirag Kisan Storage Bin 99",
            "grain_type": "pulses",
            "capacity_tonnes": 150.0,
            "current_fill_tonnes": 120.0,
            "region": "Haryana",
            "initial_moisture_pct": 11.5,
            "initial_temp_c": 22.0,
        }
        res_add = self.client.post("/api/silos", json=new_silo)
        self.assertEqual(res_add.status_code, 200)
        self.assertEqual(res_add.json()["status"], "success")

        # 2. Farmer logs custom reading
        reading = {
            "grain_moisture_pct": 14.8,  # elevated for pulses
            "temp_c": 29.0,
            "rel_humidity": 70.0,
            "notes": "Evening hand probe test"
        }
        res_read = self.client.post("/api/silos/FARMER_BIN_99/reading", json=reading)
        self.assertEqual(res_read.status_code, 200)
        read_data = res_read.json()
        self.assertIn("prediction", read_data)
        self.assertIn("playbook", read_data)

        # 3. Update farm facility profile
        farm_profile = {
            "name": "Chirag Model Organic Agro Godown",
            "region": "Haryana",
            "farmer_name": "Chirag Chanchal",
            "contact_phone": "+91 99999 88888",
            "lat": 28.4595,
            "lon": 77.0266,
        }
        res_prof = self.client.put("/api/silos/facility/profile", json=farm_profile)
        self.assertEqual(res_prof.status_code, 200)
        self.assertEqual(res_prof.json()["status"], "success")

        # 4. Clean up / Delete silo
        res_del = self.client.delete("/api/silos/FARMER_BIN_99")
        self.assertEqual(res_del.status_code, 200)

    def test_metrics_summary(self):
        res = self.client.get("/api/metrics/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("benchmarks", data)
        self.assertIn("sdg_impact", data)


if __name__ == "__main__":
    unittest.main()
