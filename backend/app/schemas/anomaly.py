from typing import Optional, Dict, Any
from pydantic import BaseModel

class AnomalyResponse(BaseModel):
    id: str
    server: str
    service: str
    title: Optional[str] = None
    time_window: Optional[str] = None
    detection_time: str
    anomaly_score: float
    confidence: int  # percentage (e.g. 91)
    severity: str    # HIGH, MEDIUM, LOW
    reason: str
    status: str      # Active, Open, Investigating, Resolved
    baseline_value: Optional[str] = None
    observed_value: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
