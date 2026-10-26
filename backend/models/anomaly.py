from typing import Optional
from pydantic import BaseModel

class Anomaly(BaseModel):
    id: str
    severity: str  # HIGH, MEDIUM, LOW
    title: str
    server: str
    service: str
    detection_time: str
    reason: str
    confidence: int  # e.g. 91
    status: str  # Active, Investigating, Resolved
    metric_name: Optional[str] = None
    baseline_value: Optional[str] = None
    observed_value: Optional[str] = None
