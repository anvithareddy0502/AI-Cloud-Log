from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.app.services.aws_log_service import aws_log_service
from backend.app.config import settings

router = APIRouter(prefix="/cloudwatch", tags=["AWS CloudWatch"])

@router.get("/status")
def get_cloudwatch_status():
    """
    Returns current AWS CloudWatch connectivity and configuration status.
    Safe to call even if AWS credentials are unconfigured.
    """
    configured = aws_log_service.is_configured()
    streams = aws_log_service.get_log_streams(limit=5) if configured else []
    
    # Mask secret key for security
    masked_key = ""
    if settings.AWS_ACCESS_KEY_ID:
        raw_key = settings.AWS_ACCESS_KEY_ID
        masked_key = f"{raw_key[:4]}...{raw_key[-4:]}" if len(raw_key) > 8 else "****"

    return {
        "status": "connected" if (configured and streams) else ("configured" if configured else "not_configured"),
        "is_configured": configured,
        "region": settings.AWS_REGION,
        "log_group": settings.AWS_LOG_GROUP,
        "access_key_masked": masked_key,
        "streams_available": len(streams),
        "message": "Connected to AWS CloudWatch" if configured else "AWS credentials not configured. Local uploads fully operational."
    }

@router.get("/streams")
def get_cloudwatch_streams(log_group: Optional[str] = Query(None)):
    """Retrieves log streams from AWS CloudWatch."""
    if not aws_log_service.is_configured():
        return {
            "configured": False,
            "message": "AWS CloudWatch not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.",
            "streams": []
        }
    streams = aws_log_service.get_log_streams(log_group_name=log_group)
    return {
        "configured": True,
        "log_group": log_group or settings.AWS_LOG_GROUP,
        "count": len(streams),
        "streams": streams
    }

@router.get("/logs")
def get_cloudwatch_logs(
    log_group: Optional[str] = Query(None),
    stream_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """Fetches recent log events from AWS CloudWatch."""
    if not aws_log_service.is_configured():
        return {
            "configured": False,
            "message": "AWS CloudWatch not configured.",
            "logs": []
        }
    logs = aws_log_service.get_cloudwatch_logs(log_group_name=log_group, log_stream_name=stream_name, limit=limit)
    return {
        "configured": True,
        "count": len(logs),
        "logs": logs
    }

@router.post("/ingest")
def ingest_cloudwatch_logs(
    log_group: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Triggers immediate ingestion of CloudWatch logs into the AI-CLAR pipeline,
    triggering ML anomaly detection and multi-factor correlation.
    """
    result = aws_log_service.ingest_from_cloudwatch(log_group_name=log_group, limit=limit)
    return result
