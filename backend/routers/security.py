from fastapi import APIRouter
from backend.database import db_manager

router = APIRouter(prefix="/api/security-events", tags=["Security"])

@router.get("")
def get_security_events():
    """Retrieve security threat events, failed attempts, and mitigation postures."""
    return db_manager.get_security_events()
