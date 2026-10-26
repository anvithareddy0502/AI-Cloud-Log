from fastapi import APIRouter
from backend.database import db_manager

router = APIRouter(prefix="/api/servers", tags=["Servers"])

@router.get("")
def get_servers():
    """Retrieve full inventory of cloud compute instances and health statuses."""
    return db_manager.get_servers()

@router.get("/health-summary")
def get_health_summary():
    """Retrieve aggregate counts of healthy, warning, and critical nodes."""
    return db_manager.get_server_health_summary()
