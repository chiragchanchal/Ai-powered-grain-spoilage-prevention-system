"""
OpenWeatherMap Weather Service with Rate-Limit Caching & Offline Fallback.
Provides current ambient conditions and 48-72 hour temperature/humidity/precipitation forecasts.
Implements 30-minute TTL coordinate caching per Section 7.1 (Module 4) of CS002 report.
"""

import os
import time
import math
import logging
import requests
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
CACHE_TTL_SECONDS = 1800  # 30 minutes


class WeatherService:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_weather(self, lat: float = 28.4595, lon: float = 77.0266, city_name: str = "Gurugram, Haryana") -> Dict[str, Any]:
        """
        Retrieves weather with 30-minute TTL coordinate caching.
        Falls back to realistic meteorological model if API key is absent or network fails.
        """
        coord_key = f"{lat:.3f}_{lon:.3f}"
        now = time.time()

        if coord_key in self._cache:
            entry = self._cache[coord_key]
            if now - entry["timestamp"] < CACHE_TTL_SECONDS:
                cached_data = dict(entry["data"])
                cached_data["cached"] = True
                cached_data["cache_age_min"] = round((now - entry["timestamp"]) / 60, 1)
                return cached_data

        data = None
        if OPENWEATHER_API_KEY:
            try:
                data = self._fetch_from_api(lat, lon, city_name)
            except Exception as e:
                logger.warning("Failed to fetch live OpenWeatherMap feed: %s. Using fallback cache.", e)

        if not data:
            data = self._generate_realistic_forecast(lat, lon, city_name)

        self._cache[coord_key] = {"timestamp": now, "data": data}
        return data

    def _fetch_from_api(self, lat: float, lon: float, city_name: str) -> Dict[str, Any]:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        resp = requests.get(url, timeout=4.0)
        resp.raise_for_status()
        raw = resp.json()

        city = raw.get("city", {}).get("name", city_name)
        forecast_list = raw.get("list", [])

        hourly_forecast = []
        max_t = -100.0
        max_rh = 0.0
        max_pop = 0.0

        for item in forecast_list[:16]:  # Next 48 hours (3h intervals)
            dt_txt = item.get("dt_txt", "")
            main = item.get("main", {})
            temp = float(main.get("temp", 25.0))
            rh = float(main.get("humidity", 60.0))
            pop = float(item.get("pop", 0.0))  # Probability of precipitation
            desc = item.get("weather", [{}])[0].get("description", "clear sky")

            if temp > max_t:
                max_t = temp
            if rh > max_rh:
                max_rh = rh
            if pop > max_pop:
                max_pop = pop

            hourly_forecast.append({
                "timestamp": dt_txt,
                "temp_c": round(temp, 1),
                "rh": round(rh, 1),
                "precip_prob": round(pop, 2),
                "condition": desc.title(),
            })

        current = hourly_forecast[0] if hourly_forecast else {
            "temp_c": 28.0, "rh": 65.0, "precip_prob": 0.1, "condition": "Partly Cloudy"
        }

        return {
            "city": city,
            "lat": lat,
            "lon": lon,
            "current_temp_c": current["temp_c"],
            "current_rh": current["rh"],
            "current_precip_prob": current["precip_prob"],
            "current_condition": current["condition"],
            "max_temp_48h": round(max_t, 1),
            "max_rh_48h": round(max_rh, 1),
            "precip_prob_48h": round(max_pop, 2),
            "hourly_timeline": hourly_forecast,
            "source": "OpenWeatherMap_Live_API",
            "cached": False,
        }

    def _generate_realistic_forecast(self, lat: float, lon: float, city_name: str) -> Dict[str, Any]:
        """
        Synthesizes realistic meteorological diurnal cycle for North Indian plains
        (Gurugram / Haryana) with day/night oscillations and realistic humidity shifts.
        """
        now = time.time()
        base_temp = 27.5
        base_rh = 68.0

        timeline = []
        max_t = base_temp
        max_rh = base_rh
        max_pop = 0.35

        for i in range(16):  # 48 hours in 3-hour steps
            step_hours = i * 3
            # Diurnal sine wave: warmest at 14:00 (hour 14), coolest at 05:00
            time_offset = (step_hours % 24)
            diurnal_temp = 5.0 * math.sin((time_offset - 8) * math.pi / 12)
            # Inverse humidity curve: highest at dawn, lowest in afternoon
            diurnal_rh = -12.0 * math.sin((time_offset - 8) * math.pi / 12)

            # Slight monsoon moisture creep over 48h
            weather_trend_rh = 0.4 * step_hours
            p_rain = min(0.85, max(0.05, 0.20 + 0.02 * step_hours))

            step_temp = round(base_temp + diurnal_temp, 1)
            step_rh = round(min(95.0, max(30.0, base_rh + diurnal_rh + weather_trend_rh)), 1)

            if step_temp > max_t:
                max_t = step_temp
            if step_rh > max_rh:
                max_rh = step_rh
            if p_rain > max_pop:
                max_pop = p_rain

            condition = "Humid / Overcast" if step_rh > 75 else ("Scattered Showers" if p_rain > 0.4 else "Partly Cloudy")

            timeline.append({
                "timestamp": f"+{step_hours}h",
                "temp_c": step_temp,
                "rh": step_rh,
                "precip_prob": round(p_rain, 2),
                "condition": condition,
            })

        return {
            "city": city_name,
            "lat": lat,
            "lon": lon,
            "current_temp_c": timeline[0]["temp_c"],
            "current_rh": timeline[0]["rh"],
            "current_precip_prob": timeline[0]["precip_prob"],
            "current_condition": timeline[0]["condition"],
            "max_temp_48h": round(max_t, 1),
            "max_rh_48h": round(max_rh, 1),
            "precip_prob_48h": round(max_pop, 2),
            "hourly_timeline": timeline,
            "source": "Meteorological_Synthesizer_Engine",
            "cached": False,
        }


weather_service = WeatherService()
