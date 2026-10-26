from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class AssistantMessage(BaseModel):
    id: str
    role: str  # user or assistant
    content: str
    timestamp: str
    citations: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = None

class AssistantQueryRequest(BaseModel):
    query: str
    context_server: Optional[str] = None
    context_incident: Optional[str] = None

class AssistantResponse(BaseModel):
    message_id: str
    answer: str
    timestamp: str
    related_server: Optional[str] = None
    related_incident_id: Optional[str] = None
    confidence_score: Optional[int] = None
    key_evidence: Optional[List[str]] = []
    suggested_followups: Optional[List[str]] = []
