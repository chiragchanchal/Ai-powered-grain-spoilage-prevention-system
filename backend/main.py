"""
Main FastAPI Application Entry Point.
Mounts REST API routers, static frontend files, and lifecycle handlers.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.routes import silos, telemetry, weather, prediction, graph, simulation, metrics

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CS002 Community Service Project — AI-Powered Grain Spoilage Prevention System for Storage Facilities",
)

# Enable CORS for cross-origin development if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(silos.router)
app.include_router(telemetry.router)
app.include_router(weather.router)
app.include_router(prediction.router)
app.include_router(graph.router)
app.include_router(simulation.router)
app.include_router(metrics.router)

# Locate Frontend Directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "facility": settings.FACILITY_NAME,
        "region": settings.DEFAULT_REGION,
    }
