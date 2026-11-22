"""
High-Performance Local Time-Series Persistence Engine.
Replicates Apache Cassandra composite partition key indexing:
((facility_id, silo_id, date_bucket), event_ts DESC)
Provides sub-millisecond rolling-window telemetry queries and historical logs.
"""

import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "grain_guard_timeseries.db")


class LocalTimeSeriesStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_tables()
        self._ensure_sample_data()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Silo registry table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS silos (
                facility_id TEXT NOT NULL,
                silo_id TEXT NOT NULL,
                name TEXT NOT NULL,
                grain_type TEXT NOT NULL,
                capacity_tonnes REAL NOT NULL,
                current_fill_tonnes REAL NOT NULL,
                installed_sensors TEXT NOT NULL,
                region TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                PRIMARY KEY (facility_id, silo_id)
            )
            """)

            # Time-series telemetry matching Cassandra schema
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS silo_telemetry (
                facility_id TEXT NOT NULL,
                silo_id TEXT NOT NULL,
                date_bucket TEXT NOT NULL,
                event_ts TIMESTAMP NOT NULL,
                temp_c REAL NOT NULL,
                rel_humidity REAL NOT NULL,
                grain_moisture_pct REAL NOT NULL,
                ext_temp_c REAL,
                ext_humidity REAL,
                precip_prob REAL,
                risk_tier TEXT DEFAULT 'LOW',
                p_risk REAL DEFAULT 0.0,
                PRIMARY KEY (facility_id, silo_id, date_bucket, event_ts)
            )
            """)

            # Facility profile table for custom farm/godown settings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS facility_profile (
                facility_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                farmer_name TEXT,
                contact_phone TEXT
            )
            """)

            # Index matching Cassandra clustering and queries
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_query 
            ON silo_telemetry (facility_id, silo_id, event_ts DESC)
            """)
            conn.commit()

    def _ensure_sample_data(self):
        """Seeds initial silos and recent telemetry history if empty."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM silos")
            if cursor.fetchone()[0] == 0:
                silos_seed = [
                    ("FAC_GURUGRAM_01", "SILO_01", "North Silo 1 - Wheat Reserve", "wheat", 500.0, 420.0, "DHT22, CapMoisture, ThermalLance", "Haryana", 28.4595, 77.0266),
                    ("FAC_GURUGRAM_01", "SILO_02", "East Silo 2 - Basmati Paddy", "paddy", 600.0, 510.0, "SHT31, CapMoisture, NDIR_CO2", "Haryana", 28.4595, 77.0266),
                    ("FAC_GURUGRAM_01", "SILO_03", "South Silo 3 - Hybrid Maize", "maize", 400.0, 310.0, "DHT22, CapMoisture", "Haryana", 28.4595, 77.0266),
                    ("FAC_GURUGRAM_01", "SILO_04", "West Silo 4 - Seed Stock Wheat", "wheat", 350.0, 280.0, "SHT31, CapMoisture, ThermalLance", "Haryana", 28.4595, 77.0266),
                ]
                cursor.executemany("""
                INSERT INTO silos (facility_id, silo_id, name, grain_type, capacity_tonnes, current_fill_tonnes, installed_sensors, region, lat, lon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, silos_seed)

                # Seed historical rolling telemetry for each silo (past 24 hours in 1-hour increments)
                now = datetime.datetime.now(datetime.timezone.utc)
                telemetry_records = []

                # SILO_01: Safe Wheat
                for h in range(24, -1, -1):
                    ts = now - datetime.timedelta(hours=h)
                    bucket = ts.strftime("%Y-%m")
                    telemetry_records.append((
                        "FAC_GURUGRAM_01", "SILO_01", bucket, ts.isoformat(),
                        23.5 + 0.05 * (24 - h), 58.2 + 0.1 * (24 - h), 12.8,
                        24.0, 60.0, 0.05, "LOW", 0.12
                    ))

                # SILO_02: Elevated Paddy (Pre-monsoon humidity drift)
                for h in range(24, -1, -1):
                    ts = now - datetime.timedelta(hours=h)
                    bucket = ts.strftime("%Y-%m")
                    t = 27.0 + 0.15 * (24 - h)
                    rh = 63.0 + 0.45 * (24 - h)
                    mc = 13.2 + 0.05 * (24 - h)
                    risk = "MEDIUM" if rh > 65.0 or mc > 13.8 else "LOW"
                    telemetry_records.append((
                        "FAC_GURUGRAM_01", "SILO_02", bucket, ts.isoformat(),
                        t, rh, mc, 28.5, 74.0, 0.45, risk, 0.48 if risk == "MEDIUM" else 0.22
                    ))

                # SILO_03: Normal Maize
                for h in range(24, -1, -1):
                    ts = now - datetime.timedelta(hours=h)
                    bucket = ts.strftime("%Y-%m")
                    telemetry_records.append((
                        "FAC_GURUGRAM_01", "SILO_03", bucket, ts.isoformat(),
                        22.0, 54.0, 12.4, 23.0, 52.0, 0.0, "LOW", 0.08
                    ))

                # SILO_04: Hotspot Alert Wheat (Thermal drift dT/dt > 0.8 C/h)
                for h in range(24, -1, -1):
                    ts = now - datetime.timedelta(hours=h)
                    bucket = ts.strftime("%Y-%m")
                    # Accelerating heating in the core
                    t = 24.0 + 0.40 * (24 - h)
                    rh = 66.0 + 0.30 * (24 - h)
                    mc = 14.6 + 0.03 * (24 - h)
                    risk = "HIGH" if h < 8 else ("MEDIUM" if h < 16 else "LOW")
                    p = 0.88 if risk == "HIGH" else (0.45 if risk == "MEDIUM" else 0.18)
                    telemetry_records.append((
                        "FAC_GURUGRAM_01", "SILO_04", bucket, ts.isoformat(),
                        t, rh, mc, 26.0, 68.0, 0.20, risk, p
                    ))

                cursor.executemany("""
                INSERT INTO silo_telemetry (facility_id, silo_id, date_bucket, event_ts, temp_c, rel_humidity, grain_moisture_pct, ext_temp_c, ext_humidity, precip_prob, risk_tier, p_risk)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, telemetry_records)
                conn.commit()

    def get_silos(self, facility_id: str = "FAC_GURUGRAM_01") -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM silos WHERE facility_id = ?", (facility_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_silo(self, silo_id: str, facility_id: str = "FAC_GURUGRAM_01") -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM silos WHERE facility_id = ? AND silo_id = ?", (facility_id, silo_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def insert_telemetry(self, data: Dict[str, Any]) -> bool:
        ts = data.get("event_ts") or datetime.datetime.now(datetime.timezone.utc).isoformat()
        date_bucket = data.get("date_bucket") or ts[:7]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO silo_telemetry 
            (facility_id, silo_id, date_bucket, event_ts, temp_c, rel_humidity, grain_moisture_pct, ext_temp_c, ext_humidity, precip_prob, risk_tier, p_risk)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
                data.get("risk_tier", "LOW"),
                float(data.get("p_risk", 0.0)),
            ))
            conn.commit()
            return True

    def get_rolling_window(self, silo_id: str, facility_id: str = "FAC_GURUGRAM_01", limit: int = 12) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM silo_telemetry 
            WHERE facility_id = ? AND silo_id = ?
            ORDER BY event_ts DESC
            LIMIT ?
            """, (facility_id, silo_id, limit))
            rows = cursor.fetchall()
            # Return in chronological order (oldest to newest in window)
            res = [dict(r) for r in rows]
            res.reverse()
            return res

    def get_latest_telemetry(self, silo_id: str, facility_id: str = "FAC_GURUGRAM_01") -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM silo_telemetry 
            WHERE facility_id = ? AND silo_id = ?
            ORDER BY event_ts DESC
            LIMIT 1
            """, (facility_id, silo_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_silo(self, silo: Dict[str, Any]) -> bool:
        """Allows farmers/operators to add their own custom storage unit."""
        facility_id = silo.get("facility_id", "FAC_GURUGRAM_01")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO silos 
            (facility_id, silo_id, name, grain_type, capacity_tonnes, current_fill_tonnes, installed_sensors, region, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                facility_id,
                silo["silo_id"],
                silo["name"],
                silo.get("grain_type", "wheat").lower(),
                float(silo.get("capacity_tonnes", 100.0)),
                float(silo.get("current_fill_tonnes", 50.0)),
                silo.get("installed_sensors", "Farmer Manual Moisture Meter, Temp Probe"),
                silo.get("region", "Haryana"),
                float(silo.get("lat", 28.4595)),
                float(silo.get("lon", 77.0266)),
            ))
            conn.commit()
            return True

    def update_silo(self, silo_id: str, data: Dict[str, Any], facility_id: str = "FAC_GURUGRAM_01") -> bool:
        """Updates crop, capacity, quantity, or name for an existing unit."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE silos SET
                name = COALESCE(?, name),
                grain_type = COALESCE(?, grain_type),
                capacity_tonnes = COALESCE(?, capacity_tonnes),
                current_fill_tonnes = COALESCE(?, current_fill_tonnes),
                region = COALESCE(?, region)
            WHERE facility_id = ? AND silo_id = ?
            """, (
                data.get("name"),
                data.get("grain_type", "").lower() if data.get("grain_type") else None,
                data.get("capacity_tonnes"),
                data.get("current_fill_tonnes"),
                data.get("region"),
                facility_id,
                silo_id,
            ))
            conn.commit()
            return True

    def delete_silo(self, silo_id: str, facility_id: str = "FAC_GURUGRAM_01") -> bool:
        """Deletes a silo and its telemetry records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM silos WHERE facility_id = ? AND silo_id = ?", (facility_id, silo_id))
            cursor.execute("DELETE FROM silo_telemetry WHERE facility_id = ? AND silo_id = ?", (facility_id, silo_id))
            conn.commit()
            return True

    def get_facility(self, facility_id: str = "FAC_GURUGRAM_01") -> Dict[str, Any]:
        """Retrieves custom farm/facility metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM facility_profile WHERE facility_id = ?", (facility_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            # Default profile
            return {
                "facility_id": facility_id,
                "name": "Gurugram Central Agro-Mandi Godown",
                "region": "Haryana",
                "lat": 28.4595,
                "lon": 77.0266,
                "farmer_name": "Authorized Mandi Supervisor",
                "contact_phone": "+91 98765 43210"
            }

    def update_facility(self, data: Dict[str, Any]) -> bool:
        """Updates custom farm or storage facility profile."""
        facility_id = data.get("facility_id", "FAC_GURUGRAM_01")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO facility_profile 
            (facility_id, name, region, lat, lon, farmer_name, contact_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                facility_id,
                data.get("name", "My Farm Grain Storage"),
                data.get("region", "Haryana"),
                float(data.get("lat", 28.4595)),
                float(data.get("lon", 77.0266)),
                data.get("farmer_name", "Farmer In-Charge"),
                data.get("contact_phone", "")
            ))
            conn.commit()
            return True


ts_store = LocalTimeSeriesStore()
