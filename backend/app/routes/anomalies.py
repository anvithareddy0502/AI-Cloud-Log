from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from backend.app.database.connection import db

router = APIRouter(tags=["Anomalies"])

@router.get("/anomalies")
def get_anomalies(
    severity: Optional[str] = Query(None, description="Filter by severity: HIGH, MEDIUM, LOW"),
    server: Optional[str] = Query(None, description="Filter by server"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Retrieves all ML-detected anomalies from MongoDB.
    """
    query = {}
    if severity and severity.upper() != "ALL":
        query["severity"] = severity.upper()
    if server and server.lower() != "all":
        query["server"] = server.lower()

    anomalies_cursor = db.anomalies.find(query, sort_by=("timestamp", -1), limit=limit)

    clean_anomalies = []
    for a in anomalies_cursor:
        clean_anomalies.append({
            "id": str(a.get("id") or a.get("_id")),
            "server": a.get("server", "server-01"),
            "service": a.get("service", "cloud-service"),
            "title": a.get("title") or f"{a.get('severity', 'HIGH')} Anomaly on {a.get('server')}",
            "time_window": a.get("time_window"),
            "detection_time": a.get("detection_time", "Recently"),
            "anomaly_score": a.get("anomaly_score", 0.85),
            "confidence": a.get("confidence", 91),
            "severity": a.get("severity", "HIGH"),
            "reason": a.get("reason", "Metric deviation detected"),
            "status": a.get("status", "Active"),
            "baseline_value": a.get("baseline_value", "Normal baseline"),
            "observed_value": a.get("observed_value", "Elevated values"),
            "features": a.get("features")
        })

    return clean_anomalies

@router.get("/anomalies/{anomaly_id}")
def get_anomaly_by_id(anomaly_id: str):
    """
    Retrieves a single ML anomaly event by ID.
    """
    anom = db.anomalies.find_one({"id": anomaly_id}) or db.anomalies.find_one({"_id": anomaly_id})
    if not anom:
        raise HTTPException(status_code=404, detail="Anomaly event not found")
    if "_id" in anom and not isinstance(anom["_id"], str):
        anom["_id"] = str(anom["_id"])
    return anom
