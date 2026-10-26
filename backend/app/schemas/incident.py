from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., description="Incident status: OPEN, INVESTIGATING, RESOLVED, IGNORED")

class IncidentItemResponse(BaseModel):
    id: str
    incident_id: str
    title: str
    severity: str
    status: str
    start_time: str
    end_time: str
    affected_servers: List[str] = Field(default_factory=list)
    affected_services: List[str] = Field(default_factory=list)
    affected_server: str = "cluster"
    affected_service: str = "system"
    related_event_ids: List[str] = Field(default_factory=list)
    related_events_count: int = 0
    root_cause: str
    likely_root_cause: str
    confidence: int
    evidence: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    detected_at: Optional[str] = None
    detected_relative: Optional[str] = None
    ai_summary: Optional[str] = None
    timeline: List[Dict[str, Any]] = Field(default_factory=list)

class IncidentListResponse(BaseModel):
    total: int
    count: int
    incidents: List[IncidentItemResponse]
