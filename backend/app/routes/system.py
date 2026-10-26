from datetime import datetime
from fastapi import APIRouter
from backend.app.database.connection import db
from backend.app.ml.anomaly_model import anomaly_model
from backend.app.services.aws_log_service import aws_log_service
from backend.app.services.alert_service import alert_service
from backend.app.config import settings

router = APIRouter(tags=["System"])

@router.get("/health")
def health_status():
    """
    Cluster and service health endpoint.
    Reports MongoDB status, log storage volume, ML model readiness, and CloudWatch state.
    """
    cw_configured = aws_log_service.is_configured()
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat(),
        "database": {
            "mode": "MongoDB" if db.is_connected else "Resilient In-Memory",
            "connected": db.is_connected,
            "total_logs": db.logs.count_documents({}),
            "total_anomalies": db.anomalies.count_documents({}),
            "total_servers": db.servers.count_documents({}),
            "total_incidents": db.incidents.count_documents({}),
            "total_alerts": db.alerts.count_documents({})
        },
        "ml_engine": {
            "model": "IsolationForest",
            "is_fitted": anomaly_model.is_fitted,
            "contamination": anomaly_model.contamination
        },
        "cloudwatch": {
            "is_configured": cw_configured,
            "region": settings.AWS_REGION if cw_configured else None,
            "log_group": settings.AWS_LOG_GROUP if cw_configured else None
        },
        "alerts": {
            "unread": alert_service.get_unread_count(),
            "total": db.alerts.count_documents({})
        }
    }

@router.get("/system/status")
def system_status():
    """Detailed operational status for Settings and administration."""
    return health_status()

@router.get("/system/counts")
def system_counts():
    """
    Returns real-time document counts from MongoDB for dynamic navigation badges
    (AI Anomalies and Incidents).
    """
    total_anomalies = db.anomalies.count_documents({})
    all_incidents = db.incidents.find()
    total_incidents = len(all_incidents)
    active_incidents = sum(
        1 for inc in all_incidents 
        if str(inc.get("status", "")).upper() in {"OPEN", "INVESTIGATING"}
    )
    return {
        "status": "success",
        "anomalies": total_anomalies,
        "total_anomalies": total_anomalies,
        "incidents": total_incidents,
        "total_incidents": total_incidents,
        "active_incidents": active_incidents,
        "total_logs": db.logs.count_documents({}),
        "unread_alerts": alert_service.get_unread_count()
    }

