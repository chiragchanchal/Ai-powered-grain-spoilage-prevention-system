-- AI-Powered Grain Spoilage Prevention System
-- Apache Cassandra Time-Series Schema Definition
-- Optimized for O(1) bounded partition retrieval and high write throughput

CREATE KEYSPACE IF NOT EXISTS grain_guard
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

CREATE TABLE IF NOT EXISTS grain_guard.silo_telemetry (
    facility_id text,
    silo_id text,
    date_bucket text,         -- e.g., '2026-11' to bound partition width
    event_ts timestamp,
    temp_c double,
    rel_humidity double,
    grain_moisture_pct double,
    ext_temp_c double,
    ext_humidity double,
    precip_prob double,
    risk_tier text,           -- 'LOW', 'MEDIUM', 'HIGH'
    PRIMARY KEY ((facility_id, silo_id, date_bucket), event_ts)
) WITH CLUSTERING ORDER BY (event_ts DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_risk ON grain_guard.silo_telemetry (risk_tier);
