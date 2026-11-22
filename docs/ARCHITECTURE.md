# AgroGuard AI: System Architecture Specification

## 1. Architectural Overview

The **AI-Powered Grain Spoilage Prevention System** implements an asynchronous, four-tier data-to-decision architecture designed to transition rural grain storage facilities, mandis, and farmer producer organizations (FPOs) from reactive loss discovery to proactive, weather-aware spoilage prevention.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      TIER 1: DATA INGESTION                            │
│  IoT Silo Sensors (Temp, RH, Moisture) + OpenWeatherMap 48h API       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 TIER 2: HYBRID POLYGLOT PERSISTENCE                    │
│  Apache Cassandra (Time-Series CQL) + Neo4j (Climate Knowledge Graph) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   TIER 3: PREDICTIVE AI ENGINE                         │
│  9-Dim Feature Vector + Dual Ensemble (55% Random Forest + 45% MLP)    │
│  FAO & ASABE Psychrometric Thresholds (Dew Point, EMC, Thermal Drift)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                TIER 4: ACTIONABLE OPERATOR DASHBOARD                   │
│  Interactive Web UI (Tailwind + Gauges + 3D Silos + Bi-Lingual EN/HI)  │
│  Preventive Action Playbooks + Scenario Stress Tester + Reports        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Tier Specifications

### Tier 1: Ingestion & Meteorological Feeds
- **IoT Sensor Telemetry**: Silo temperature probes (DHT22/SHT31), capacitive interstitial moisture sensors, and thermal probe lances.
- **Meteorological Forecast**: Scheduled poller fetching current conditions and 48–72 hour forecasts (temperature, relative humidity, precipitation probability) from OpenWeatherMap.
- **Coordinate-Level Cache**: 30-minute Time-To-Live (TTL) cache prevents quota exhaustion and protects against rural internet outages.

### Tier 2: Hybrid Polyglot Persistence
- **Time-Series Storage (Apache Cassandra)**:
  - Partition Key: `((facility_id, silo_id, date_bucket), event_ts DESC)`
  - Guarantees $O(1)$ partition retrieval without relational table scan overhead.
  - Accompanied by a local zero-dependency fallback store (`sqlite_timeseries.py`) that replicates the exact partition indexing for development and standalone evaluation.
- **Climate Knowledge Graph (Neo4j & NetworkX)**:
  - Captures multi-hop agro-climatic relationships:
    `(Region)-[:EXPERIENCES]->(ClimateEvent)-[:TRIGGERS]->(SpoilageType)<-[:SUSCEPTIBLE_TO]-(GrainType)`
  - Returns a normalized domain prior score ($kg\_prior \in [0.0, 1.0]$) and ASABE pathogen-specific mitigation instructions.

### Tier 3: Feature Engineering & Dual ML Inference Engine
1. **Feature Vector ($\mathbf{x} \in \mathbb{R}^9$)**:
   - $x_0 = T_{internal}$ (Current storage temperature, °C)
   - $x_1 = RH_{internal}$ (Current interstitial relative humidity, %)
   - $x_2 = MC_{grain}$ (Current grain moisture percentage, %)
   - $x_3 = \frac{dT}{dt}$ (Thermal drift rate over 6h rolling window, °C/hr)
   - $x_4 = \frac{dRH}{dt}$ (Humidity drift rate over 6h rolling window, %/hr)
   - $x_5 = T_{ext, 48h}^{max}$ (Forecasted maximum external ambient temperature, °C)
   - $x_6 = RH_{ext, 48h}^{max}$ (Forecasted maximum external relative humidity, %)
   - $x_7 = P(precip_{48h})$ (Forecasted 48-hour precipitation probability, $0.0 - 1.0$)
   - $x_8 = kg\_prior$ (Knowledge graph regional climate risk prior score)

2. **Dual-Model Weighted Ensemble**:
   $$P(High) = 0.55 \cdot P_{RF}(High) + 0.45 \cdot P_{NN}(High)$$
   - **Random Forest**: 120 decision trees with balanced class weighting for tabular threshold precision and feature importance interpretability.
   - **Deep Neural Network**: Multi-layer perceptron (64x32 hidden layers, ReLU activation, Adam optimizer) for complex multi-parameter interactions.

3. **High-Recall Safety Overrides**:
   - In commercial storage, failing to detect a critical hotspot or moisture bloom causes catastrophic bin spoilage.
   - Override rule: If $MC > 14.5\%$, or ($RH \ge 68\%$ and $T \ge 28^\circ C$), or $\frac{dT}{dt} \ge 0.45^\circ C/hr$, risk tier is escalated to `HIGH` regardless of base classification.

### Tier 4: Community Presentation & Operator Playbook
- **Interactive Web Interface**: Live SVG gauges, 3D grain cutaways, dark/light theme, and real-time audio alert synthesis.
- **Bi-Lingual Support**: Full English and Hindi (हिन्दी) translations for rural godown attendants.
- **Psychrometric Aeration Engine**: Evaluates dew point, equilibrium moisture content (EMC via Modified Oswin equation), and prevents ventilation during high ambient humidity or rain.
- **Stress-Testing Engine**: Injects simulated pre-monsoon spikes, biological heating hotspots, and roof moisture leaks for validation and demonstration.
