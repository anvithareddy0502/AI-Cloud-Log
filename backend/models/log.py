from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class CloudLog(BaseModel):
    id: str
    timestamp: str
    server: str
    service: str
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    latency_ms: Optional[int] = None
    ip_address: Optional[str] = None
    environment: Optional[str] = "production-aws"
    stack_trace: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LogFilterParams(BaseModel):
    server: Optional[str] = None
    service: Optional[str] = None
    severity: Optional[str] = None
    search: Optional[str] = None
    time_range: Optional[str] = "24h"
    limit: int = 100
    skip: int = 0
