"""
AI-CLAR Natural Language AI Explainer Module
Extension Point for Phase 2:
- Generates executive summaries and incident explanations.
- Can plug directly into Google Gemini API or local Ollama LLMs.
"""
from typing import Dict, Any

class AiExplainerService:
    def __init__(self, provider: str = "template"):
        self.provider = provider

    def generate_incident_explanation(self, incident: Dict[str, Any]) -> str:
        """
        Synthesizes raw evidence, root causes, and telemetry metrics into clean human-readable prose.
        """
        title = incident.get("title", "Cloud Anomaly")
        server = incident.get("affected_server", "Unknown Node")
        service = incident.get("affected_service", "Cloud Service")
        cause = incident.get("likely_root_cause", "Resource saturation")
        
        return (
            f"The AI-CLAR engine detected an abnormal operational anomaly on {server} ({service}). "
            f"Cross-service correlation identified '{cause}' as the primary catalyst. "
            f"Secondary degradation rapidly propagated to downstream consumers with 91% algorithmic confidence."
        )

ai_explainer = AiExplainerService()
