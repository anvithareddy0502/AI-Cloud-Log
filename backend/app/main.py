from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database.connection import db
from backend.app.utils.logger import logger
from backend.app.routes import (
    logs, dashboard, anomalies, servers, system, incidents, security, assistant,
    cloudwatch, alerts, reports, ml
)

# Retain Phase 1 router for reports
from backend.routers import reports as p1_reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI-CLAR Engine...")
    db.connect()
    logger.info("AI-CLAR ready on %s:%d (Environment: %s)", settings.HOST, settings.PORT, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down AI-CLAR Engine...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-Based Cloud Log Correlation, Anomaly Detection and Root-Cause Analysis",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Core Routers (both root and /api prefixes for full proxy/direct compatibility)
for prefix in ["", "/api"]:
    app.include_router(system.router, prefix=prefix)
    app.include_router(logs.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(anomalies.router, prefix=prefix)
    app.include_router(servers.router, prefix=prefix)
    app.include_router(incidents.router, prefix=prefix)
    app.include_router(security.router, prefix=prefix)
    app.include_router(assistant.router, prefix=prefix)
    app.include_router(cloudwatch.router, prefix=prefix)
    app.include_router(alerts.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)
    app.include_router(ml.router, prefix=prefix)

# Register Reports Router
app.include_router(p1_reports.router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "phase": "Phase 2: Log Ingestion, Normalization, MongoDB & ML Anomaly Detection",
        "docs_url": "/docs",
        "database_status": "MongoDB" if db.is_connected else "Resilient In-Memory"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
