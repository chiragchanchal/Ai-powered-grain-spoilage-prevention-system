# AgroGuard AI: REST API Reference

The backend REST API is built with FastAPI, providing self-documenting OpenAPI schemas at `/docs` and `/redoc`.

Base URL: `http://localhost:8000`

---

## 1. Silo Management

### `GET /api/silos`
Returns all registered storage units within the current facility alongside their latest telemetry, psychrometric calculations, risk classifications, and operational playbooks.

**Sample Response:**
```json
{
  "facility_id": "FAC_GURUGRAM_01",
  "facility_name": "Gurugram Central Agro-Mandi Godown",
  "total_silos": 4,
  "high_risk_count": 0,
  "medium_risk_count": 1,
  "low_risk_count": 3,
  "silos": [
    {
      "silo_id": "SILO_01",
      "name": "North Silo 1 - Wheat Reserve",
      "grain_type": "wheat",
      "capacity_tonnes": 500.0,
      "current_fill_tonnes": 420.0,
      "fill_percentage": 84.0,
      "telemetry": {
        "temp_c": 23.5,
        "rel_humidity": 58.2,
        "grain_moisture_pct": 12.8,
        "dew_point_c": 14.6,
        "emc_pct": 12.1,
        "dt_dt": 0.05
      },
      "risk_assessment": {
        "risk_tier": "LOW",
        "p_risk": 0.12,
        "primary_command": "OPTIMAL STORAGE: Grain microclimate is stable within safe FAO limits",
        "primary_command_hi": "सुरक्षित स्थिति: अनाज का तापमान और नमी सुरक्षित सीमा में है",
        "fan_action": "OFF"
      }
    }
  ]
}
```

### `GET /api/silos/{silo_id}`
Returns details and 24-hour rolling history for a specific silo.

---

## 2. Telemetry Ingestion

### `POST /api/telemetry/ingest`
Ingests a single IoT sensor packet, runs the dual ML ensemble, updates the time-series store, and generates an updated playbook.

**Request Body:**
```json
{
  "silo_id": "SILO_01",
  "facility_id": "FAC_GURUGRAM_01",
  "temp_c": 24.2,
  "rel_humidity": 61.0,
  "grain_moisture_pct": 13.1
}
```

**Response:**
```json
{
  "status": "success",
  "ingested_timestamp": "2026-11-22T11:15:00Z",
  "silo_id": "SILO_01",
  "risk_tier": "LOW",
  "p_high": 0.18,
  "playbook": {
    "fan_action": "OFF",
    "can_aerate": false,
    "dew_point_c": 16.1
  }
}
```

---

## 3. Weather Integration

### `GET /api/weather/current`
Returns current ambient conditions and 48-hour hourly forecasts with coordinate caching.

---

## 4. Machine Learning & What-If Inference

### `POST /api/predict`
Direct inference endpoint for evaluating custom storage parameters and hypothetical weather conditions.

**Request Body:**
```json
{
  "grain_type": "wheat",
  "region": "Haryana",
  "temp_c": 32.0,
  "rel_humidity": 76.0,
  "grain_moisture_pct": 14.8,
  "dt_dt": 0.45,
  "max_temp_48h": 36.0,
  "max_rh_48h": 82.0,
  "precip_prob_48h": 0.65
}
```

---

## 5. Climate Knowledge Graph

### `GET /api/graph/visualization`
Returns nodes and edges formatted for frontend interactive canvas rendering.

### `GET /api/graph/query`
Queries the graph risk prior for a specified region, grain variety, and climate threshold.

---

## 6. Stress Scenario Simulation

### `GET /api/simulation/scenarios`
Lists available demonstration stress scenarios:
- `monsoon_spike`: Pre-monsoon humidity surge & incoming storm
- `hotspot_heating`: Biological self-heating in core grain stack
- `moisture_leak`: High dampness roof leak
- `safe_winter`: Stabilized cold dry storage

### `POST /api/simulation/trigger`
Injects a scenario into the designated silo and evaluates real-time impact.

### `POST /api/simulation/reset`
Restores all silos to verified safe baseline states.

---

## 7. Metrics & SDG Impact

### `GET /api/metrics/summary`
Returns benchmark evaluations (Accuracy, High-Risk Recall, Latency), model metadata, and UN SDG 2, 12, 13 baseline vs outcome assessments.
