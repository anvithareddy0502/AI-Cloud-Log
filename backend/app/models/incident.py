from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class IncidentStatus:
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"
    ALL = [OPEN, INVESTIGATING, RESOLVED, IGNORED]

class IncidentSeverity:
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    ALL = [CRITICAL, HIGH, MEDIUM, LOW]

class IncidentModel(BaseModel):
    incident_id: str
    title: str
    severity: str = "HIGH"
    status: str = IncidentStatus.OPEN
    start_time: str
    end_time: str
    affected_servers: List[str] = Field(default_factory=list)
    affected_services: List[str] = Field(default_factory=list)
    related_event_ids: List[str] = Field(default_factory=list)
    root_cause: str = "Under Investigation"
    confidence: int = 50
    evidence: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    
    # UI compatibility attributes
    ai_summary: Optional[str] = None
    timeline: List[Dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Returns normalized dictionary with UI compatibility aliases."""
        data = self.model_dump()
        data["id"] = self.incident_id
        data["affected_server"] = self.affected_servers[0] if self.affected_servers else "cluster"
        data["affected_service"] = self.affected_services[0] if self.affected_services else "system"
        data["likely_root_cause"] = self.root_cause
        data["recommended_actions"] = self.recommendations
        data["related_events_count"] = len(self.related_event_ids)
        data["detected_at"] = self.start_time
        data["detected_relative"] = "Recently detected"
        return data
