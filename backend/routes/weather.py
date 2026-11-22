"""
Meteorological Weather Integration Endpoints.
"""

from fastapi import APIRouter
from backend.services.weather_service import weather_service
from backend.config import settings

router = APIRouter(prefix="/api/weather", tags=["Weather"])


@router.get("/current", summary="Get live meteorological telemetry and 48h forecast")
def get_current_weather(lat: float = settings.DEFAULT_LAT, lon: float = settings.DEFAULT_LON):
    return weather_service.get_weather(lat=lat, lon=lon, city_name="Gurugram, Haryana")
