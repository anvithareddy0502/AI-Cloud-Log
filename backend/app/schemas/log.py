from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class LogRecord(BaseModel):
    id: str
    timestamp: str
    server: str
    service: str
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    ip: Optional[str] = None
    ip_address: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    latency_ms: Optional[int] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    correlation_id: Optional[str] = None
    stack_trace: Optional[str] = None

class LogUploadResponse(BaseModel):
    total_records: int
    successfully_parsed: int
    failed_records: int
    anomalies_detected: int
    errors: List[str]

class LogListResponse(BaseModel):
    total: int
    count: int
    limit: int
    skip: int
    logs: List[LogRecord]
