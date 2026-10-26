import time
from datetime import datetime
from fastapi import APIRouter
from backend.models.assistant import AssistantQueryRequest, AssistantResponse
from backend.data.mock_data import ASSISTANT_KNOWLEDGE
from backend.database import db_manager

router = APIRouter(prefix="/api/assistant", tags=["AI Assistant"])

@router.post("/chat", response_model=AssistantResponse)
def query_assistant(req: AssistantQueryRequest):
    """
    Endpoint for AI Cloud Assistant.
    Provides structured analysis, telemetry evidence, and recommendations.
    Can be connected directly to LLM providers (e.g. Gemini, OpenAI, Claude) in Phase 2.
    """
    q = req.query.lower()
    
    # Match query intent
    matched_key = None
    if "critical" in q or "error" in q:
        matched_key = "critical"
    elif "server-03" in q or "server 03" in q or "server 3" in q or "fail" in q:
        matched_key = "server-03"
    elif "security" in q or "threat" in q or "attack" in q:
        matched_key = "security"
    elif "problem" in q or "which server" in q or "most" in q:
        matched_key = "problems"
    elif "latest" in q or "cause" in q or "recent" in q:
        matched_key = "latest"
    else:
        # Default intelligent response
        return AssistantResponse(
            message_id=f"msg-{int(time.time()*1000)}",
            answer=(
                f"Based on real-time telemetry from 27 monitored cloud instances, "
                f"the primary active alert is on **Server-03** (Payment API / Database connection timeout, 327 events). "
                f"There is also an active security alert on **Server-02** (47 failed login attempts).\n\n"
                f"Feel free to click any of the suggested queries or ask specifically about a server, error code, or incident."
            ),
            timestamp=datetime.now().strftime("%H:%M:%S"),
            related_server="Server-03",
            related_incident_id="inc-01",
            confidence_score=90,
            key_evidence=[
                "Database pool reached 99.4% saturation",
                "Payment API response latency +63%"
            ],
            suggested_followups=[
                "Why did Server-03 fail?",
                "What are today's critical errors?",
                "Are there any security threats?"
            ]
        )
        
    data = ASSISTANT_KNOWLEDGE[matched_key]
    return AssistantResponse(
        message_id=f"msg-{int(time.time()*1000)}",
        answer=data["answer"],
        timestamp=datetime.now().strftime("%H:%M:%S"),
        related_server=data.get("related_server"),
        related_incident_id=data.get("related_incident_id"),
        confidence_score=data.get("confidence_score", 91),
        key_evidence=data.get("evidence", []),
        suggested_followups=data.get("suggested_followups", [])
    )
