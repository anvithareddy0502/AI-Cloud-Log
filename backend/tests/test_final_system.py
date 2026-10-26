import pytest
from datetime import datetime, timezone

from backend.app.database.connection import db
from backend.app.models.incident import IncidentModel, IncidentStatus, IncidentSeverity
from backend.app.services.log_parser import log_parser
from backend.app.services.anomaly_detector import anomaly_detector_service
from backend.app.services.event_correlator import event_correlator
from backend.app.services.root_cause_engine import root_cause_engine
from backend.app.services.ai_explainer import ai_explainer
from backend.app.services.security_detector import security_detector
from backend.app.services.alert_service import alert_service
from backend.app.services.report_generator import report_generator
from backend.app.services.aws_log_service import aws_log_service

# ====================================================================
# SCENARIO 1: Normal logs ingestion does NOT trigger incidents or false alerts
# ====================================================================
def test_scenario_1_normal_logs_no_incidents():
    normal_logs = [
        {"id": "norm-1", "timestamp": "2026-09-07 10:00:00", "server": "srv-web", "service": "web-server", "severity": "INFO", "message": "GET /index.html 200 OK", "status_code": 200, "cpu_usage": 20.0, "memory_usage": 35.0},
        {"id": "norm-2", "timestamp": "2026-09-07 10:01:00", "server": "srv-web", "service": "web-server", "severity": "INFO", "message": "GET /static/app.css 200 OK", "status_code": 200, "cpu_usage": 22.0, "memory_usage": 36.0},
        {"id": "norm-3", "timestamp": "2026-09-07 10:02:00", "server": "srv-db", "service": "database", "severity": "INFO", "message": "Connection established for user read_only", "status_code": 200, "cpu_usage": 15.0, "memory_usage": 40.0}
    ]
    # Verify candidate filter ignores standard INFO traffic
    candidates = [l for l in normal_logs if event_correlator.is_candidate_event(l)]
    assert len(candidates) == 0, "Normal INFO logs must not be marked as incident candidates"
    
    incidents = event_correlator.cluster_events(normal_logs)
    assert len(incidents) == 0, "No incident clusters should form from normal traffic"

# ====================================================================
# SCENARIO 2: Single server error anomaly detection
# ====================================================================
def test_scenario_2_single_server_error_anomaly():
    error_logs = [
        {"id": "err-1", "timestamp": "2026-09-07 10:15:00", "server": "srv-auth", "service": "auth-service", "severity": "ERROR", "message": "Disk space critically low: 98% full", "status_code": 500, "cpu_usage": 85.0, "memory_usage": 92.0}
    ]
    assert event_correlator.is_candidate_event(error_logs[0]) is True
    clusters = event_correlator.cluster_events(error_logs)
    assert len(clusters) == 1
    assert clusters[0][0]["server"] == "srv-auth"

# ====================================================================
# SCENARIO 3: Cascading failure across dependent services grouped into ONE incident
# ====================================================================
def test_scenario_3_cascading_failure_correlation():
    # Database pool exhaustion -> Payment API timeout -> Web server 504
    cascade_logs = [
        {"id": "casc-1", "timestamp": "2026-09-07 10:20:00", "server": "srv-db", "service": "database", "severity": "CRITICAL", "message": "PostgreSQL: remaining connection slots are reserved for non-replication superuser connections", "status_code": 500},
        {"id": "casc-2", "timestamp": "2026-09-07 10:20:30", "server": "srv-api", "service": "payment-api", "severity": "ERROR", "message": "HikariCP-1 failed to acquire connection from database within 30000ms: pool exhausted", "status_code": 503},
        {"id": "casc-3", "timestamp": "2026-09-07 10:21:00", "server": "srv-web", "service": "web-server", "severity": "ERROR", "message": "upstream payment-api timed out (504 Gateway Timeout) on /checkout", "status_code": 504}
    ]
    clusters = event_correlator.cluster_events(cascade_logs)
    assert len(clusters) == 1, f"Cascading logs should form exactly 1 cluster, but got {len(clusters)}"
    assert len(clusters[0]) == 3, "All 3 cascading events should be grouped together"

# ====================================================================
# SCENARIO 4: Unrelated errors on different servers remain strictly separate
# ====================================================================
def test_scenario_4_unrelated_errors_remain_separate():
    unrelated_logs = [
        {"id": "unrel-1", "timestamp": "2026-09-07 08:00:00", "server": "srv-media", "service": "transcoder", "severity": "ERROR", "message": "FFmpeg audio codec initialization failed", "status_code": 500},
        {"id": "unrel-2", "timestamp": "2026-09-07 14:30:00", "server": "srv-analytics", "service": "reporting-worker", "severity": "ERROR", "message": "CSV export write permission denied on /mnt/data", "status_code": 500}
    ]
    clusters = event_correlator.cluster_events(unrelated_logs)
    assert len(clusters) == 2, f"Unrelated events across distinct services/times should form 2 clusters, got {len(clusters)}"

# ====================================================================
# SCENARIO 5: Incident generation with all required fields
# ====================================================================
def test_scenario_5_incident_model_fields():
    incident = IncidentModel(
        incident_id="inc-test-01",
        title="Test Database Connectivity Failure",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        start_time="2026-09-07 10:00:00",
        end_time="2026-09-07 10:05:00",
        affected_servers=["srv-01", "srv-02"],
        affected_services=["Database", "API Gateway"],
        related_event_ids=["log-1", "log-2"],
        root_cause="Database pool saturation under sudden traffic spike",
        confidence=92,
        evidence=["HikariCP timeout", "Postgres max connections exceeded"],
        recommendations=["Increase connection pool size", "Add read replicas"],
        created_at="2026-09-07 10:05:00",
        updated_at="2026-09-07 10:05:00"
    )
    data = incident.to_dict()
    required_keys = [
        "incident_id", "title", "severity", "status", "start_time", "end_time",
        "affected_servers", "affected_services", "related_event_ids", "root_cause",
        "confidence", "evidence", "recommendations", "created_at", "updated_at"
    ]
    for key in required_keys:
        assert key in data, f"Field '{key}' is missing in IncidentModel dictionary"
    assert data["confidence"] == 92
    assert data["status"] == "OPEN"

# ====================================================================
# SCENARIO 6: Evidence-based AI explanation has all 6 structured sections
# ====================================================================
def test_scenario_6_evidence_based_ai_explanation():
    incident_dict = {
        "id": "inc-rca-test",
        "title": "Database Connection Pool Exhaustion",
        "severity": "CRITICAL",
        "status": "OPEN",
        "affected_servers": ["srv-db-01"],
        "affected_services": ["PostgreSQL"],
        "likely_root_cause": "Database connection exhaustion",
        "confidence": 93,
        "evidence": [
            "psql: fatal: remaining connection slots reserved",
            "HikariCP pool limit 100/100 connections saturated"
        ],
        "timeline": [
            {"time": "10:00:00", "server": "srv-db-01", "service": "PostgreSQL", "event": "Remaining connection slots reserved", "severity": "CRITICAL"}
        ],
        "recommended_actions": [
            "Scale up connection pool max-connections",
            "Terminate orphan idle connections"
        ]
    }
    explanation = ai_explainer.explain_incident(incident_dict)
    
    sections = [
        "what_happened",
        "why_it_was_detected",
        "likely_root_cause",
        "affected_services",
        "evidence",
        "recommended_actions"
    ]
    for sec in sections:
        assert sec in explanation, f"Section '{sec}' missing in AI explanation"
        assert len(explanation[sec]) > 0, f"Section '{sec}' is empty"

    # Verify no hallucination: mentions PostgreSQL and connection exhaustion
    assert "postgresql" in explanation["what_happened"].lower() or "database" in explanation["what_happened"].lower()
    assert "connection" in explanation["likely_root_cause"].lower()

# ====================================================================
# SCENARIO 7: Insufficient evidence returns standardized truthful fallback
# ====================================================================
def test_scenario_7_insufficient_evidence_fallback():
    sparse_incident = {
        "id": "inc-sparse",
        "title": "Unknown Telemetry Flap",
        "severity": "LOW",
        "confidence": 30,
        "evidence": [],
        "timeline": [],
        "likely_root_cause": "Insufficient evidence"
    }
    explanation = ai_explainer.explain_incident(sparse_incident)
    assert "Insufficient evidence" in explanation["likely_root_cause"] or "insufficient evidence" in explanation["what_happened"].lower()

# ====================================================================
# SCENARIO 8: Security anomaly detection detects brute force & stores event
# ====================================================================
def test_scenario_8_security_anomaly_detection():
    auth_burst = []
    for i in range(15):
        auth_burst.append({
            "id": f"sec-log-{i}",
            "timestamp": f"2026-09-07 11:00:{i:02d}",
            "server": "Server-02",
            "service": "Authentication",
            "severity": "WARNING",
            "message": f"Failed password for invalid user admin{i} from 198.51.100.42 port 4421{i} ssh2",
            "status_code": 401,
            "ip": "198.51.100.42"
        })
    sec_events = security_detector.detect_security_events(auth_burst)
    assert len(sec_events) > 0, "High-frequency failed logins must trigger security event"
    event = sec_events[0]
    assert event["event_type"] in ["BRUTE_FORCE_ATTACK", "SUSPICIOUS_LOGIN_BURST", "EXCESSIVE_FAILED_LOGINS", "Repeated Failed Logins"]
    assert "198.51.100.42" in str(event.get("source_ip") or event.get("details", ""))
    assert event["risk_level"] in ["HIGH", "CRITICAL"] or event["severity"] in ["HIGH", "CRITICAL"]

# ====================================================================
# SCENARIO 9: Alert system creates alert for CRITICAL incident and marks read
# ====================================================================
def test_scenario_9_alert_system():
    critical_incident = {
        "incident_id": "inc-crit-999",
        "id": "inc-crit-999",
        "title": "Catastrophic Core Database Failure",
        "severity": "CRITICAL",
        "affected_servers": ["Server-03"],
        "affected_services": ["Database Primary"],
        "root_cause": "Disk hardware I/O error on NVMe storage array",
        "confidence": 98
    }
    alert = alert_service.create_alert_for_incident(critical_incident)
    assert alert is not None, "Alert must be created for CRITICAL incident"
    assert alert["severity"] == "CRITICAL"
    assert alert["incident_id"] == "inc-crit-999"
    assert alert["read"] is False

    # Retrieve alerts
    alerts_list = alert_service.get_alerts(unread_only=True)
    found = any(a.get("incident_id") == "inc-crit-999" for a in alerts_list)
    assert found is True, "Newly created alert must appear in unread alerts list"

    # Mark as read
    res = alert_service.mark_alert_read(alert["alert_id"])
    assert res is True, "Marking alert read should succeed"
    updated_alert = db.alerts.find_one({"alert_id": alert["alert_id"]})
    assert updated_alert["read"] is True

# ====================================================================
# SCENARIO 10: PDF incident report generation & unconfigured AWS fallback
# ====================================================================
def test_scenario_10_pdf_report_and_aws_fallback():
    # 1. PDF Report Generation
    test_incident = {
        "incident_id": "inc-pdf-01",
        "title": "Payment API Gateway Timeout Incident",
        "severity": "CRITICAL",
        "status": "INVESTIGATING",
        "start_time": "2026-09-07 12:00:00",
        "end_time": "2026-09-07 12:15:00",
        "affected_servers": ["srv-payment-01", "srv-db-01"],
        "affected_services": ["Payment API", "PostgreSQL"],
        "root_cause": "TCP connection exhaustion on database connection pool",
        "confidence": 94,
        "evidence": [
            "504 Gateway Timeout count surged by 340%",
            "Active connections pool reached 100/100 limit"
        ],
        "timeline": [
            {"time": "12:00:00", "server": "srv-db-01", "service": "PostgreSQL", "severity": "CRITICAL", "event": "Max connections reached"},
            {"time": "12:01:00", "server": "srv-payment-01", "service": "Payment API", "severity": "ERROR", "event": "HikariCP acquisition timeout"}
        ],
        "recommendations": [
            "Tune connection pool idle timeouts",
            "Enable connection pooling proxy like PgBouncer"
        ]
    }
    pdf_bytes = report_generator.generate_pdf(test_incident)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000, "PDF document must be substantial"
    assert pdf_bytes.startswith(b"%PDF"), "Generated file must start with %PDF header"

    # 2. AWS CloudWatch Graceful Fallback
    # When credentials are not configured, methods must return graceful fallbacks without raising
    is_cfg = aws_log_service.is_configured()
    assert isinstance(is_cfg, bool)
    groups = aws_log_service.get_log_groups()
    assert isinstance(groups, list)
    streams = aws_log_service.get_log_streams()
    assert isinstance(streams, list)
    recent = aws_log_service.get_recent_events()
    assert isinstance(recent, list)


# ====================================================================
# SCENARIO 11: Dynamic System Counts for Navigation Badges
# ====================================================================
def test_scenario_11_dynamic_system_counts():
    from backend.app.routes.system import system_counts
    res = system_counts()
    assert res["status"] == "success"
    assert "anomalies" in res
    assert "incidents" in res
    assert "active_incidents" in res
    assert "total_anomalies" in res
    assert "total_incidents" in res
    assert res["total_anomalies"] == db.anomalies.count_documents({})
    assert res["total_incidents"] == db.incidents.count_documents({})

