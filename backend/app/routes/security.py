from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from backend.app.database.connection import db
from backend.app.utils.logger import logger

router = APIRouter(tags=["Security"])

@router.get("/security-events")
def get_security_events(
    risk_level: Optional[str] = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)"),
    server: Optional[str] = Query(None, description="Filter by server"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, MITIGATED, REVIEWED)"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0)
) -> List[Dict[str, Any]]:
    """
    Retrieves real security anomaly events from MongoDB with filtering support.
    """
    query: Dict[str, Any] = {}
    if risk_level and risk_level.lower() != "all":
        query["risk_level"] = risk_level.upper()
    if server and server.lower() != "all":
        query["server"] = {"$regex": server, "$options": "i"}
    if event_type and event_type.lower() != "all":
        query["event_type"] = {"$regex": event_type, "$options": "i"}
    if status and status.lower() != "all":
        query["status"] = status.upper()

    events = db.security_events.find(query, sort_by=("timestamp", -1), limit=limit, skip=skip)
    
    # Normalize ID for frontend
    clean_events = []
    for ev in events:
        d = dict(ev)
        d["id"] = str(d.get("id") or d.get("_id"))
        if "_id" in d and not isinstance(d["_id"], str):
            d["_id"] = str(d["_id"])
        clean_events.append(d)

    return clean_events

@router.get("/security-events/{event_id}")
def get_security_event_by_id(event_id: str) -> Dict[str, Any]:
    """
    Retrieves detailed security audit information for a specific event.
    """
    event = db.security_events.find_one({"id": event_id}) or db.security_events.find_one({"_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail=f"Security event '{event_id}' not found.")
    d = dict(event)
    d["id"] = str(d.get("id") or d.get("_id"))
    return d
