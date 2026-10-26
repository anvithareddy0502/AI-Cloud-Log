from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter
from backend.app.services.ai_assistant import ai_assistant
from backend.app.utils.logger import logger

router = APIRouter(tags=["AI Assistant"])

class AiAskRequest(BaseModel):
    question: Optional[str] = Field(None, description="Natural language question")
    query: Optional[str] = Field(None, description="Query alias for frontend compatibility")
    context_server: Optional[str] = None
    context_incident: Optional[str] = None

class AiAskResponse(BaseModel):
    message_id: str
    answer: str
    timestamp: str
    related_server: Optional[str] = None
    related_incident_id: Optional[str] = None
    confidence_score: int = 90
    key_evidence: List[str] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)

@router.post("/ai/ask", response_model=AiAskResponse)
def ask_ai(req: AiAskRequest):
    """
    Primary AI Assistant endpoint:
    Grounds answers in real MongoDB telemetry (servers, incidents, logs, anomalies, security events).
    """
    user_query = req.question or req.query or ""
    result = ai_assistant.answer_question(user_query)
    now_time = datetime.now(timezone.utc).strftime("%H:%M:%S")

    return AiAskResponse(
        message_id=f"msg-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        answer=result["answer"],
        timestamp=now_time,
        related_server=result.get("related_server"),
        related_incident_id=result.get("related_incident_id"),
        confidence_score=result.get("confidence_score", 90),
        key_evidence=result.get("key_evidence", []),
        suggested_followups=result.get("suggested_followups", [])
    )

@router.post("/assistant/chat", response_model=AiAskResponse)
def assistant_chat_alias(req: AiAskRequest):
    """
    Compatibility alias endpoint for /assistant/chat.
    """
    return ask_ai(req)
