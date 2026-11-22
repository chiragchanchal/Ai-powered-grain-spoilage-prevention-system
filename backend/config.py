"""
System Configuration & Environment Variables.
"""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    APP_NAME: str = "AI Grain Spoilage Prevention System"
    APP_VERSION: str = "2.0.0"
    FACILITY_ID: str = os.getenv("FACILITY_ID", "FAC_GURUGRAM_01")
    FACILITY_NAME: str = os.getenv("FACILITY_NAME", "Gurugram Central Agro-Mandi Godown")
    DEFAULT_REGION: str = os.getenv("DEFAULT_REGION", "Haryana")
    DEFAULT_LAT: float = float(os.getenv("DEFAULT_LAT", "28.4595"))
    DEFAULT_LON: float = float(os.getenv("DEFAULT_LON", "77.0266"))
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    CASSANDRA_HOSTS: str = os.getenv("CASSANDRA_HOSTS", "localhost")
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
