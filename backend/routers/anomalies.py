from fastapi import APIRouter
from backend.database import db_manager

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies"])

@router.get("")
def get_anomalies():
    """Retrieve all AI detected anomalies with confidence ratings and baseline deviations."""
    return db_manager.get_anomalies()
