from datetime import datetime
from fastapi import APIRouter, HTTPException
from backend.models.report import ReportGenerateRequest, IncidentReport
from backend.database import db_manager

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("")
def get_reports():
    """Retrieve post-mortem incident reports."""
    return db_manager.get_reports()

@router.post("/generate")
def generate_report(request: ReportGenerateRequest):
    """Generates a structured post-mortem report for an incident."""
    incident = db_manager.get_incident_by_id(request.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    report_id = f"rep-{int(datetime.now().timestamp())}"
    new_report = {
        "id": report_id,
        "incident_id": incident["id"],
        "title": f"Executive Post-Mortem: {incident['title']}",
        "severity": incident["severity"],
        "server": incident["affected_server"],
        "service": incident["affected_service"],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Generated",
        "summary": incident["ai_summary"],
        "likely_root_cause": incident["likely_root_cause"],
        "impact_scope": f"{incident['affected_service']} running on {incident['affected_server']}",
        "mitigation_steps": incident["recommended_actions"],
        "author": "AI-CLAR Automated RCA Engine"
    }
    db_manager.add_report(new_report)
    return new_report
