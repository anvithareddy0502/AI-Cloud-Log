import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import db_manager
from backend.routers import (
    dashboard,
    logs,
    incidents,
    anomalies,
    security,
    servers,
    reports,
    assistant
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aiclar.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Try connecting to database
    logger.info("Initializing AI-CLAR Backend...")
    db_manager.connect()
    logger.info(
        "AI-CLAR ready on %s:%d (Environment: %s)",
        settings.HOST, settings.PORT, settings.ENVIRONMENT
    )
    yield
    # Shutdown
    logger.info("Shutting down AI-CLAR Backend...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-Based Cloud Log Correlation, Anomaly Detection and Root-Cause Analysis API",
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

# Register Routers
app.include_router(dashboard.router)
app.include_router(logs.router)
app.include_router(incidents.router)
app.include_router(anomalies.router)
app.include_router(security.router)
app.include_router(servers.router)
app.include_router(reports.router)
app.include_router(assistant.router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "database_mode": "MongoDB" if db_manager.is_connected_to_mongo else "Resilient In-Memory"
    }

@app.get("/healthz")
def health_check():
    return {
        "status": "healthy",
        "timestamp": str(logging.Formatter().formatTime(logging.LogRecord("", 0, "", 0, "", (), None))),
        "mongo_connected": db_manager.is_connected_to_mongo
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
