import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.database.connection import db
from backend.app.utils.logger import logger

class AlertService:
    """
    Alert Dispatch and Management Service.
    Automatically generates and stores system alerts when critical incidents
    or security anomalies are detected.
    """

    def create_alert_for_incident(self, incident: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Creates an alert if the incident is CRITICAL.
        Deduplicates if an unread alert for this incident already exists.
        """
        sev = str(incident.get("severity", "")).upper()
        if sev not in {"CRITICAL", "HIGH"}:
            return None

        inc_id = incident.get("incident_id") or incident.get("id")
        if not inc_id:
            return None

        # Deduplication: check if an unread alert already exists for this incident
        existing = db.alerts.find_one({"incident_id": inc_id, "read": False})
        if existing:
            logger.info("Alert already active for incident %s; skipping duplicate.", inc_id)
            return existing

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        alert_id = f"alt-{uuid.uuid4().hex[:8]}"

        servers_str = ", ".join(incident.get("affected_servers", [])) or incident.get("affected_server", "Unknown Server")
        services_str = ", ".join(incident.get("affected_services", [])) or incident.get("affected_service", "Unknown Service")
        title = incident.get("title", "Critical Incident Detected")
        root_cause = incident.get("root_cause") or incident.get("likely_root_cause") or "Investigating root cause"

        message = (
            f"CRITICAL Incident on {servers_str} ({services_str}): {title}. "
            f"Root Cause: {root_cause}."
        )

        alert_doc = {
            "alert_id": alert_id,
            "incident_id": inc_id,
            "title": f"CRITICAL: {title}",
            "severity": sev,
            "message": message,
            "created_at": now_str,
            "read": False
        }

        db.alerts.insert_one(alert_doc)
        logger.warning("ALERT DISPATCHED [%s] for Incident %s: %s", alert_id, inc_id, title)
        return alert_doc

    def get_alerts(self, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves stored alerts, sorted with newest first."""
        query = {}
        if unread_only:
            query["read"] = False
        alerts = db.alerts.find(query=query, sort_by=("created_at", -1), limit=limit)
        return alerts

    def mark_alert_read(self, alert_id: str) -> bool:
        """Marks an alert as read."""
        alert = db.alerts.find_one({"alert_id": alert_id})
        if not alert:
            # Also check by _id or id
            alert = db.alerts.find_one({"id": alert_id})
        if not alert:
            return False

        target_id = alert.get("alert_id") or alert.get("id") or alert.get("_id")
        db.alerts.update_one({"alert_id": target_id}, {"$set": {"read": True}})
        return True

    def mark_all_read(self) -> int:
        """Marks all active alerts as read."""
        unread_alerts = db.alerts.find({"read": False})
        count = len(unread_alerts)
        for a in unread_alerts:
            aid = a.get("alert_id") or a.get("id")
            db.alerts.update_one({"alert_id": aid}, {"$set": {"read": True}})
        return count

    def get_unread_count(self) -> int:
        """Returns the total number of unread alerts."""
        return db.alerts.count_documents({"read": False})

alert_service = AlertService()

def create_alert_for_incident(incident: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return alert_service.create_alert_for_incident(incident)

def get_alerts(unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
    return alert_service.get_alerts(unread_only=unread_only, limit=limit)

def mark_alert_read(alert_id: str) -> bool:
    return alert_service.mark_alert_read(alert_id)
