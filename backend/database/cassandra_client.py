"""
Apache Cassandra Client with automatic fallback to high-throughput LocalTimeSeriesStore.
Guarantees consistent time-series storage whether Cassandra is running or running in local mode.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from .sqlite_timeseries import ts_store

logger = logging.getLogger(__name__)

CASSANDRA_HOSTS = os.getenv("CASSANDRA_HOSTS", "localhost").split(",")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "grain_guard")


class CassandraConnector:
    def __init__(self):
        self.cluster = None
        self.session = None
        self.is_connected = False
        self._init_connection()

    def _init_connection(self):
        try:
            from cassandra.cluster import Cluster
            self.cluster = Cluster(CASSANDRA_HOSTS, connect_timeout=3.0)
            self.session = self.cluster.connect()
            self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
            """)
            self.session.set_keyspace(CASSANDRA_KEYSPACE)
            self.is_connected = True
            logger.info("Connected successfully to Apache Cassandra cluster at %s", CASSANDRA_HOSTS)
        except Exception as e:
            self.is_connected = False
            logger.info("Apache Cassandra not active (%s). Operating with local time-series store.", e)

    def insert_telemetry(self, data: Dict[str, Any]) -> bool:
        # Always write to local store for UI fast reads
        ts_store.insert_telemetry(data)

        if self.is_connected and self.session:
            try:
                query = f"""
                INSERT INTO {CASSANDRA_KEYSPACE}.silo_telemetry (
                    facility_id, silo_id, date_bucket, event_ts,
                    temp_c, rel_humidity, grain_moisture_pct,
                    ext_temp_c, ext_humidity, precip_prob, risk_tier
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                ts = data.get("event_ts")
                date_bucket = data.get("date_bucket") or ts[:7]
                self.session.execute(query, (
                    data["facility_id"],
                    data["silo_id"],
                    date_bucket,
                    ts,
                    float(data["temp_c"]),
                    float(data["rel_humidity"]),
                    float(data["grain_moisture_pct"]),
                    float(data.get("ext_temp_c", 25.0)),
                    float(data.get("ext_humidity", 60.0)),
                    float(data.get("precip_prob", 0.0)),
                    data.get("risk_tier", "LOW")
                ))
            except Exception as ex:
                logger.warning("Failed Cassandra write: %s", ex)
        return True

    def get_rolling_window(self, silo_id: str, facility_id: str = "FAC_GURUGRAM_01", limit: int = 12) -> List[Dict[str, Any]]:
        return ts_store.get_rolling_window(silo_id, facility_id, limit)

    def get_latest_telemetry(self, silo_id: str, facility_id: str = "FAC_GURUGRAM_01") -> Optional[Dict[str, Any]]:
        return ts_store.get_latest_telemetry(silo_id, facility_id)

    def get_silos(self, facility_id: str = "FAC_GURUGRAM_01") -> List[Dict[str, Any]]:
        return ts_store.get_silos(facility_id)

    def get_silo(self, silo_id: str, facility_id: str = "FAC_GURUGRAM_01") -> Optional[Dict[str, Any]]:
        return ts_store.get_silo(silo_id, facility_id)

    def close(self):
        if self.cluster:
            self.cluster.shutdown()


cassandra_connector = CassandraConnector()
