import io
from datetime import datetime, timezone
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class IncidentReportGenerator:
    """
    Generates downloadable PDF incident investigation reports using ReportLab.
    Produces high-fidelity, professional, structured documents containing:
    - Incident Overview & Metadata
    - Root Cause Analysis & Confidence Score
    - Affected Cloud Infrastructure (Servers & Services)
    - Timeline of Correlated Events
    - Evidence Breakdown
    - AI Explanation & Recommended Actions
    """

    def generate_pdf(self, incident: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Palette
        PRIMARY_BLUE = colors.HexColor("#1e3a8a")     # Deep corporate navy blue
        ACCENT_BLUE = colors.HexColor("#2563eb")      # Vibrant blue
        TEXT_DARK = colors.HexColor("#1e293b")        # Slate dark
        TEXT_MUTED = colors.HexColor("#64748b")       # Muted slate
        BG_LIGHT = colors.HexColor("#f8fafc")         # Light slate background
        BORDER_COLOR = colors.HexColor("#e2e8f0")     # Subtle border

        # Severity color
        sev_str = str(incident.get("severity", "MEDIUM")).upper()
        if "CRIT" in sev_str:
            SEV_COLOR = colors.HexColor("#dc2626")    # Red
        elif "HIGH" in sev_str or "WARN" in sev_str:
            SEV_COLOR = colors.HexColor("#d97706")    # Amber
        else:
            SEV_COLOR = colors.HexColor("#2563eb")    # Blue

        # Custom Typography
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=PRIMARY_BLUE
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=TEXT_MUTED
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=PRIMARY_BLUE,
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=TEXT_DARK
        )
        body_bold = ParagraphStyle(
            "DocBodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=TEXT_DARK
        )
        code_style = ParagraphStyle(
            "DocCode",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#334155")
        )

        elements = []

        # 1. Header Banner
        inc_id = incident.get("incident_id") or incident.get("id", "INC-001")
        title = incident.get("title", "Cloud Incident Investigation Report")
        elements.append(Paragraph("AI-CLAR CLOUD OBSERVABILITY & RCA PLATFORM", subtitle_style))
        elements.append(Spacer(1, 2))
        elements.append(Paragraph(f"Incident Investigation Report: {inc_id}", title_style))
        elements.append(Spacer(1, 4))
        
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        elements.append(Paragraph(f"Generated On: <b>{now_str}</b> | System Classification: <b>Production</b>", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceBefore=0, spaceAfter=8))

        # 2. Metadata Summary Table
        status = str(incident.get("status", "OPEN")).upper()
        conf = incident.get("confidence", 85)
        start_ts = incident.get("start_time") or incident.get("detected_at") or incident.get("created_at", "N/A")
        end_ts = incident.get("end_time", "Ongoing")
        servers = ", ".join(incident.get("affected_servers", [])) or incident.get("affected_server", "All Nodes")
        services = ", ".join(incident.get("affected_services", [])) or incident.get("affected_service", "Core Services")

        meta_data = [
            [
                Paragraph("<b>Incident Title:</b>", body_bold),
                Paragraph(title, body_style),
                Paragraph("<b>Severity:</b>", body_bold),
                Paragraph(f"<font color='{SEV_COLOR.hexval()}'><b>{sev_str}</b></font>", body_style)
            ],
            [
                Paragraph("<b>Status:</b>", body_bold),
                Paragraph(f"<b>{status}</b>", body_style),
                Paragraph("<b>RCA Confidence:</b>", body_bold),
                Paragraph(f"<b>{conf}%</b>", body_style)
            ],
            [
                Paragraph("<b>Start Timestamp:</b>", body_bold),
                Paragraph(str(start_ts), body_style),
                Paragraph("<b>End / Last Event:</b>", body_bold),
                Paragraph(str(end_ts), body_style)
            ],
            [
                Paragraph("<b>Affected Nodes:</b>", body_bold),
                Paragraph(servers, body_style),
                Paragraph("<b>Affected Services:</b>", body_bold),
                Paragraph(services, body_style)
            ]
        ]

        meta_table = Table(meta_data, colWidths=[105, 165, 110, 160])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 10))

        # 3. Root Cause Analysis
        elements.append(Paragraph("1. DETERMINISTIC ROOT CAUSE ANALYSIS", h2_style))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=2, spaceAfter=6))
        
        root_cause = incident.get("root_cause") or incident.get("likely_root_cause") or "Under Investigation"
        elements.append(Paragraph(f"<b>Primary Root Cause:</b> {root_cause}", body_style))
        elements.append(Spacer(1, 4))
        
        ai_summary = incident.get("ai_summary", "")
        if ai_summary:
            elements.append(Paragraph(f"<b>Executive Summary:</b> {ai_summary}", body_style))
            elements.append(Spacer(1, 6))

        # 4. Evidence List
        elements.append(Paragraph("2. VERIFIED EVIDENCE & TELEMETRY ANOMALIES", h2_style))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=2, spaceAfter=6))
        
        evidence_list = incident.get("evidence", [])
        if evidence_list and isinstance(evidence_list, list):
            for ev in evidence_list:
                elements.append(Paragraph(f"• {ev}", body_style))
                elements.append(Spacer(1, 2))
        else:
            elements.append(Paragraph("• No secondary telemetry anomalies logged for this incident.", body_style))
        elements.append(Spacer(1, 6))

        # 5. Timeline of Events
        timeline = incident.get("timeline", [])
        if timeline and isinstance(timeline, list) and len(timeline) > 0:
            elements.append(Paragraph("3. CORRELATED EVENT TIMELINE", h2_style))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=2, spaceAfter=6))

            t_rows = [
                [
                    Paragraph("<b>Timestamp</b>", body_bold),
                    Paragraph("<b>Node</b>", body_bold),
                    Paragraph("<b>Service</b>", body_bold),
                    Paragraph("<b>Severity</b>", body_bold),
                    Paragraph("<b>Event Log Message</b>", body_bold)
                ]
            ]
            for item in timeline[:12]:  # Limit to 12 rows for clean layout
                t_rows.append([
                    Paragraph(str(item.get("time") or item.get("timestamp", "")), code_style),
                    Paragraph(str(item.get("server", "")), code_style),
                    Paragraph(str(item.get("service", "")), code_style),
                    Paragraph(str(item.get("severity", "")), code_style),
                    Paragraph(str(item.get("event") or item.get("message", "")), body_style),
                ])

            timeline_table = Table(t_rows, colWidths=[80, 60, 80, 50, 270])
            timeline_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(timeline_table)
            elements.append(Spacer(1, 8))

        # 6. AI Incident Explanation
        ai_exp = incident.get("ai_explanation")
        if ai_exp and isinstance(ai_exp, dict):
            elements.append(Paragraph("4. EVIDENCE-BASED AI EXPLANATION", h2_style))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=2, spaceAfter=6))
            
            elements.append(Paragraph(f"<b>What Happened:</b> {ai_exp.get('what_happened', 'N/A')}", body_style))
            elements.append(Spacer(1, 2))
            elements.append(Paragraph(f"<b>Why Detected:</b> {ai_exp.get('why_it_was_detected', 'N/A')}", body_style))
            elements.append(Spacer(1, 2))
            elements.append(Paragraph(f"<b>Likely Root Cause:</b> {ai_exp.get('likely_root_cause', 'N/A')}", body_style))
            elements.append(Spacer(1, 2))
            elements.append(Paragraph(f"<b>Affected Services:</b> {ai_exp.get('affected_services', 'N/A')}", body_style))
            elements.append(Spacer(1, 6))

        # 7. Recommended Remediation Actions
        recs = incident.get("recommendations") or incident.get("recommended_actions", [])
        elements.append(Paragraph("5. RECOMMENDED REMEDIATION ACTIONS", h2_style))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=2, spaceAfter=6))
        
        if recs and isinstance(recs, list):
            for r in recs:
                elements.append(Paragraph(f"✓ {r}", body_style))
                elements.append(Spacer(1, 2))
        else:
            elements.append(Paragraph("✓ Monitor server metrics and verify service health status.", body_style))

        elements.append(Spacer(1, 14))
        elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_BLUE, spaceBefore=4, spaceAfter=4))
        elements.append(Paragraph("CONFIDENTIAL & PROPRIETARY — AI-CLAR CLOUD INCIDENT INTELLIGENCE", subtitle_style))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

report_generator = IncidentReportGenerator()

def generate_incident_pdf(incident: Dict[str, Any]) -> bytes:
    return report_generator.generate_pdf(incident)
