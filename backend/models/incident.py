from typing import List, Optional
from pydantic import BaseModel

class TimelineEvent(BaseModel):
    time: str
    server: str
    service: str
    event: str
    severity: str

class Incident(BaseModel):
    id: str
    title: str
    severity: str  # Critical, High, Medium, Low
    affected_server: str
    affected_service: str
    detected_at: str
    detected_relative: str
    status: str  # Investigating, Open, Resolved
    related_events_count: int
    ai_summary: str
    evidence: List[str]
    likely_root_cause: str
    confidence: int  # percentage, e.g. 91
    recommended_actions: List[str]
    timeline: Optional[List[TimelineEvent]] = []
