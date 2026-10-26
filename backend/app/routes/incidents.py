from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from backend.app.database.connection import db
from backend.app.models.incident import IncidentStatus
from backend.app.schemas.incident import IncidentStatusUpdate
from backend.app.services.ai_explainer import ai_explainer
from backend.app.utils.logger import logger

router = APIRouter(tags=["Incidents"])

@router.get("/incidents")
def get_incidents(
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, INVESTIGATING, RESOLVED, IGNORED)"),
    server: Optional[str] = Query(None, description="Filter by affected server"),
    service: Optional[str] = Query(None, description="Filter by affected service"),
    start_time: Optional[str] = Query(None, description="Start timestamp"),
    end_time: Optional[str] = Query(None, description="End timestamp"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0)
) -> List[Dict[str, Any]]:
    """
    Retrieves all correlated cloud incidents with filtering capabilities.
    """
    query: Dict[str, Any] = {}
    if severity and severity.lower() != "all":
        query["severity"] = severity.upper()
    if status and status.lower() != "all":
        query["status"] = status.upper()
    if server and server.lower() != "all":
        query["$or"] = [
            {"affected_servers": {"$regex": server, "$options": "i"}},
            {"affected_server": {"$regex": server, "$options": "i"}}
        ]
    if service and service.lower() != "all":
        query["$or"] = [
            {"affected_services": {"$regex": service, "$options": "i"}},
            {"affected_service": {"$regex": service, "$options": "i"}}
        ]
    if start_time and end_time:
        query["start_time"] = {"$gte": start_time, "$lte": end_time}
    elif start_time:
        query["start_time"] = {"$gte": start_time}
    elif end_time:
        query["end_time"] = {"$lte": end_time}

    incidents = db.incidents.find(query, sort_by=("updated_at", -1), limit=limit, skip=skip)
    
    # Normalize dictionary fields for frontend compatibility
    results = []
    for inc in incidents:
        results.append(_normalize_incident_doc(inc))
    return results

@router.get("/incidents/{incident_id}")
def get_incident_by_id(incident_id: str) -> Dict[str, Any]:
    """
    Retrieves complete incident details, including chronological timeline,
    RCA likely root cause, evidence metrics, actionable recommendations, and structured AI analysis.
    """
    inc = db.incidents.find_one({"incident_id": incident_id}) or db.incidents.find_one({"id": incident_id})
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    doc = _normalize_incident_doc(inc)
    # Attach structured AI explanation
    doc["ai_explanation"] = ai_explainer.explain_incident(incident_id)
    return doc

@router.get("/incidents/{incident_id}/ai-explanation")
def get_ai_incident_explanation(incident_id: str) -> Dict[str, Any]:
    """
    Retrieves structured evidence-based AI explanation:
    WHAT HAPPENED, WHY IT WAS DETECTED, LIKELY ROOT CAUSE, AFFECTED SERVICES, EVIDENCE, RECOMMENDED ACTIONS.
    """
    return ai_explainer.explain_incident(incident_id)

@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str) -> Dict[str, Any]:
    """
    Marks an incident as RESOLVED.
    """
    return _update_incident_status_internal(incident_id, IncidentStatus.RESOLVED)

@router.post("/incidents/{incident_id}/ignore")
def ignore_incident(incident_id: str) -> Dict[str, Any]:
    """
    Marks an incident as IGNORED.
    """
    return _update_incident_status_internal(incident_id, IncidentStatus.IGNORED)

@router.post("/incidents/{incident_id}/status")
def update_incident_status(incident_id: str, update: IncidentStatusUpdate) -> Dict[str, Any]:
    """
    Updates status of an incident (OPEN, INVESTIGATING, RESOLVED, IGNORED).
    """
    normalized_status = update.status.upper()
    if normalized_status not in IncidentStatus.ALL:
        # Fallback if UI passes TitleCase
        if normalized_status in ["OPEN", "INVESTIGATING", "RESOLVED", "IGNORED"]:
            pass
        elif update.status.capitalize() in ["Open", "Investigating", "Resolved", "Ignored"]:
            normalized_status = update.status.upper()
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status '{update.status}'. Allowed: {', '.join(IncidentStatus.ALL)}"
            )
    return _update_incident_status_internal(incident_id, normalized_status)

def _update_incident_status_internal(incident_id: str, new_status: str) -> Dict[str, Any]:
    inc = db.incidents.find_one({"incident_id": incident_id}) or db.incidents.find_one({"id": incident_id})
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    
    target_id = inc.get("incident_id") or inc.get("id")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    db.incidents.update_one(
        {"$or": [{"incident_id": target_id}, {"id": target_id}]},
        {"$set": {"status": new_status, "updated_at": now_str}}
    )
    
    updated = db.incidents.find_one({"$or": [{"incident_id": target_id}, {"id": target_id}]})
    logger.info("Incident '%s' status transitioned to '%s'.", target_id, new_status)
    return {
        "message": f"Incident status updated to {new_status}",
        "incident": _normalize_incident_doc(updated or inc)
    }

def _normalize_incident_doc(inc: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures both model-standard and frontend-compatible keys exist."""
    res = dict(inc)
    inc_id = str(res.get("incident_id") or res.get("id") or res.get("_id", "inc-unknown"))
    res["id"] = inc_id
    res["incident_id"] = inc_id

    # Servers & services
    servers = res.get("affected_servers") or ([res.get("affected_server")] if res.get("affected_server") else ["cluster"])
    services = res.get("affected_services") or ([res.get("affected_service")] if res.get("affected_service") else ["system"])
    res["affected_servers"] = servers
    res["affected_services"] = services
    res["affected_server"] = servers[0] if servers else "cluster"
    res["affected_service"] = services[0] if services else "system"

    # RCA aliases
    rc = res.get("root_cause") or res.get("likely_root_cause") or "Under Investigation"
    res["root_cause"] = rc
    res["likely_root_cause"] = rc

    recs = res.get("recommendations") or res.get("recommended_actions") or []
    res["recommendations"] = recs
    res["recommended_actions"] = recs

    res["related_event_ids"] = res.get("related_event_ids", [])
    res["related_events_count"] = res.get("related_events_count") or len(res["related_event_ids"])

    if "start_time" not in res and "detected_at" in res:
        res["start_time"] = res["detected_at"]
    if "detected_at" not in res and "start_time" in res:
        res["detected_at"] = res["start_time"]

    res.setdefault("end_time", res.get("start_time", ""))
    res.setdefault("created_at", res.get("start_time", ""))
    res.setdefault("updated_at", res.get("created_at", ""))
    res.setdefault("detected_relative", "recently")
    res.setdefault("timeline", [])

    if "_id" in res and not isinstance(res["_id"], str):
        res["_id"] = str(res["_id"])

    return res
