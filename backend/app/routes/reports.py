from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
from backend.app.database.connection import db
from backend.app.services.report_generator import report_generator

router = APIRouter(tags=["Incident Reports"])

@router.get("/incidents/{incident_id}/report")
def get_incident_report_pdf(incident_id: str):
    """
    Generates and downloads a real, comprehensive PDF Incident Investigation Report
    using ReportLab based on actual incident telemetry.
    """
    # Look up incident in database
    incident = db.incidents.find_one({"incident_id": incident_id})
    if not incident:
        incident = db.incidents.find_one({"id": incident_id})
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    pdf_bytes = report_generator.generate_pdf(incident)

    filename = f"AI-CLAR-Report-{incident_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
