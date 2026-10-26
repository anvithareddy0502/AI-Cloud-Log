from fastapi import APIRouter
from backend.database import db_manager

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats():
    """Returns top 4 KPI cards, cloud health breakdown, prominent AI incident, charts, and recent incidents."""
    return db_manager.get_dashboard_stats()
