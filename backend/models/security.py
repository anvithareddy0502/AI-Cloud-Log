from typing import Optional
from pydantic import BaseModel

class SecurityEvent(BaseModel):
    id: str
    title: str
    server: str
    service: str
    timestamp: str
    source_ip: str
    source_geo: Optional[str] = "Unknown Location"
    attempt_count: int
    severity: str  # Critical, High, Medium, Low
    risk_level: str  # Critical, High, Medium, Low
    details: str
    status: str  # Blocked, Monitored, Under Review
    action_taken: str
