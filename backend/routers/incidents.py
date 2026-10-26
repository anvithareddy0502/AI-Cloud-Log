from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.database import db_manager

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

class IncidentStatusUpdate(BaseModel):
    status: str  # Investigating, Open, Resolved

@router.get("")
def get_incidents():
    """Retrieve all detected incidents with AI summary and status."""
    return db_manager.get_incidents()

@router.get("/{incident_id}")
def get_incident_by_id(incident_id: str):
    """Retrieve in-depth incident details, evidence metrics, likely root cause, confidence, and action items."""
    incident = db_manager.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.post("/{incident_id}/status")
def update_incident_status(incident_id: str, update: IncidentStatusUpdate):
    """Update status of an incident (Investigating, Open, Resolved)."""
    incident = db_manager.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident["status"] = update.status
    return {"message": "Incident status updated", "incident": incident}
