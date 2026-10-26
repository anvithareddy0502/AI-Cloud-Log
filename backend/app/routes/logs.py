import os
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from backend.app.config import settings
from backend.app.database.connection import db
from backend.app.services.log_parser import log_parser
from backend.app.services.anomaly_detector import anomaly_detector_service
from backend.app.services.event_correlator import event_correlator
from backend.app.services.security_detector import security_detector
from backend.app.services.health_calculator import health_calculator
from backend.app.schemas.log import LogUploadResponse, LogListResponse, LogRecord
from backend.app.utils.logger import logger

router = APIRouter(tags=["Logs"])

@router.post("/logs/upload", response_model=LogUploadResponse)
async def upload_logs(file: UploadFile = File(...)):
    """
    Ingests and parses .log, .txt, .csv, and .json files.
    Fault-tolerant parsing: skips and captures malformed lines.
    Automatically triggers ML anomaly detection and recalculates cluster health.
    """
    # 1. Validate extension
    filename = file.filename or "upload.log"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed extensions are: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Read content with size check
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if len(content) == 0:
        return LogUploadResponse(
            total_records=0,
            successfully_parsed=0,
            failed_records=0,
            anomalies_detected=0,
            errors=["Uploaded file is empty."]
        )

    # 3. Parse and normalize
    parsed_logs, parse_errors = log_parser.parse_file(filename, content)
    total_records = len(parsed_logs) + len(parse_errors)

    # 4. Store in MongoDB logs collection
    if parsed_logs:
        try:
            db.logs.insert_many(parsed_logs)
            logger.info("Ingested %d valid log records from '%s'.", len(parsed_logs), filename)
        except Exception as e:
            logger.error("Database ingestion error: %s", e)
            raise HTTPException(status_code=500, detail="Failed to store logs in database.")

    # 5. Run ML Anomaly Detection on newly ingested batch
    new_anomalies = []
    if parsed_logs:
        try:
            new_anomalies = anomaly_detector_service.process_and_detect(parsed_logs)
        except Exception as e:
            logger.error("Error during ML anomaly detection: %s", e)

    # 5.5 Run Event Correlation and Incident Generation
    new_incidents = []
    if parsed_logs:
        try:
            new_incidents = event_correlator.correlate_and_create_incidents(parsed_logs)
            logger.info("Correlated events and created/updated %d incidents.", len(new_incidents))
        except Exception as e:
            logger.error("Error during event correlation and incident generation: %s", e)

    # 5.6 Run Cyber Security Anomaly Detection
    new_security_events = []
    if parsed_logs:
        try:
            new_security_events = security_detector.process_logs(parsed_logs)
            if new_security_events:
                logger.info("Security detector identified %d security anomaly event(s).", len(new_security_events))
        except Exception as e:
            logger.error("Error during security anomaly detection: %s", e)

    # 6. Recalculate cluster health
    try:
        health_calculator.recalculate_all_servers()
    except Exception as e:
        logger.error("Error updating server health metrics: %s", e)

    return LogUploadResponse(
        total_records=total_records,
        successfully_parsed=len(parsed_logs),
        failed_records=len(parse_errors),
        anomalies_detected=len(new_anomalies),
        errors=parse_errors[:20]  # Cap error messages to avoid payload bloat
    )

@router.get("/logs")
def get_logs(
    server: Optional[str] = Query(None, description="Filter by server"),
    service: Optional[str] = Query(None, description="Filter by service"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    search: Optional[str] = Query(None, description="Text search in message"),
    start_time: Optional[str] = Query(None, description="ISO or string start timestamp"),
    end_time: Optional[str] = Query(None, description="ISO or string end timestamp"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """
    Retrieves filtered, paginated cloud logs from MongoDB.
    """
    query = {}
    if server and server.lower() != "all":
        query["server"] = server.lower()
    if service and service.lower() != "all":
        query["service"] = service.lower().replace(" ", "-")
    if severity and severity.lower() != "all":
        query["severity"] = severity.upper()
    if search:
        query["$or"] = [
            {"message": {"$regex": search, "$options": "i"}},
            {"server": {"$regex": search, "$options": "i"}},
            {"correlation_id": {"$regex": search, "$options": "i"}}
        ]
    if start_time and end_time:
        query["timestamp"] = {"$gte": start_time, "$lte": end_time}
    elif start_time:
        query["timestamp"] = {"$gte": start_time}
    elif end_time:
        query["timestamp"] = {"$lte": end_time}

    total = db.logs.count_documents(query)
    logs_cursor = db.logs.find(query, sort_by=("timestamp", -1), limit=limit, skip=skip)

    # Format output records
    clean_logs = []
    for l in logs_cursor:
        clean_logs.append({
            "id": str(l.get("id") or l.get("_id")),
            "timestamp": l.get("timestamp", ""),
            "server": l.get("server", "server-01"),
            "service": l.get("service", "web-server"),
            "severity": l.get("severity", "INFO"),
            "message": l.get("message", ""),
            "ip": l.get("ip"),
            "ip_address": l.get("ip_address") or l.get("ip"),
            "status_code": l.get("status_code"),
            "response_time": l.get("response_time"),
            "latency_ms": l.get("latency_ms"),
            "cpu_usage": l.get("cpu_usage"),
            "memory_usage": l.get("memory_usage"),
            "correlation_id": l.get("correlation_id"),
            "stack_trace": l.get("stack_trace")
        })

    return {
        "total": total,
        "count": len(clean_logs),
        "limit": limit,
        "skip": skip,
        "logs": clean_logs
    }

@router.get("/logs/{log_id}")
def get_log_by_id(log_id: str):
    """
    Retrieves full raw log details for a single event.
    """
    log = db.logs.find_one({"id": log_id}) or db.logs.find_one({"_id": log_id})
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    if "_id" in log and not isinstance(log["_id"], str):
        log["_id"] = str(log["_id"])
    return log
