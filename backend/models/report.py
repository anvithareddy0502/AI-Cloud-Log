from typing import List, Optional
from pydantic import BaseModel

class IncidentReport(BaseModel):
    id: str
    incident_id: str
    title: str
    severity: str
    server: str
    service: str
    date: str
    status: str  # Generated, Pending Review, Archived
    summary: str
    likely_root_cause: str
    impact_scope: str
    mitigation_steps: List[str]
    author: str = "AI-CLAR Automated Engine"

class ReportGenerateRequest(BaseModel):
    incident_id: str
