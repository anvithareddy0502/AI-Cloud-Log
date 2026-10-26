from fastapi import APIRouter, HTTPException, Query
from backend.app.services.alert_service import alert_service

router = APIRouter(prefix="/alerts", tags=["Alert System"])

@router.get("")
@router.get("/")
def get_alerts(unread_only: bool = Query(False), limit: int = Query(50, ge=1, le=100)):
    """
    Retrieves system alerts. Filterable by unread status.
    """
    alerts_list = alert_service.get_alerts(unread_only=unread_only, limit=limit)
    unread_count = alert_service.get_unread_count()
    return {
        "total": len(alerts_list),
        "unread": unread_count,
        "alerts": alerts_list
    }

@router.post("/{alert_id}/read")
def mark_alert_read(alert_id: str):
    """
    Marks a specific alert as read.
    """
    success = alert_service.mark_alert_read(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return {
        "success": True,
        "alert_id": alert_id,
        "read": True
    }

@router.post("/mark-all-read")
def mark_all_alerts_read():
    """
    Marks all existing alerts as read.
    """
    count = alert_service.mark_all_read()
    return {
        "success": True,
        "marked_read_count": count
    }
