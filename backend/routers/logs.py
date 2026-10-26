from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.database import db_manager

router = APIRouter(prefix="/api/logs", tags=["Logs"])

@router.get("")
def get_logs(
    server: Optional[str] = Query(None, description="Filter by server ID e.g. Server-01"),
    service: Optional[str] = Query(None, description="Filter by service name e.g. Payment API"),
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, WARNING, ERROR, CRITICAL"),
    search: Optional[str] = Query(None, description="Search query in log messages or correlation IDs"),
    time_range: Optional[str] = Query("24h", description="Time range: 15m, 1h, 24h, 7d"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """Fetch paginated, searchable, filterable cloud logs."""
    return db_manager.get_logs(
        server=server,
        service=service,
        severity=severity,
        search=search,
        limit=limit,
        skip=skip
    )

@router.get("/{log_id}")
def get_log_by_id(log_id: str):
    """Retrieve full raw log details, including stack trace and correlation metadata."""
    log = db_manager.get_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return log
