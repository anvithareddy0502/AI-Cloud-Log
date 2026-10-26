import pytest
from backend.app.services.ai_explainer import ai_explainer
from backend.app.services.security_detector import security_detector, RiskLevel
from backend.app.services.ai_assistant import ai_assistant
from backend.app.database.connection import db

def test_a_ai_explanation_using_real_incident():
    """
    Test A: AI explanation using a real incident produces structured, fact-grounded sections:
    WHAT HAPPENED, WHY DETECTED, LIKELY ROOT CAUSE, AFFECTED SERVICES, EVIDENCE, RECOMMENDED ACTIONS.
    """
    # Use existing seeded incident inc-01 or seed one
    inc = db.incidents.find_one({"id": "inc-01"})
    assert inc is not None, "Pre-seeded incident inc-01 not found in database"

    explanation = ai_explainer.explain_incident("inc-01")
    assert explanation["has_sufficient_evidence"] is True
    assert "what_happened" in explanation
    assert "why_it_was_detected" in explanation
    assert "likely_root_cause" in explanation
    assert "affected_services" in explanation
    assert "evidence" in explanation
    assert "recommended_actions" in explanation
    assert len(explanation["evidence"]) > 0
    assert len(explanation["recommended_actions"]) > 0
    assert explanation["confidence"] > 0
    assert "database" in explanation["likely_root_cause"].lower() or "connection" in explanation["likely_root_cause"].lower()

def test_b_ai_does_not_fabricate_missing_evidence():
    """
    Test B: AI does not fabricate missing evidence when an incident has no telemetry.
    Must return explicit "Insufficient evidence to determine a confident root cause."
    """
    # 1. Non-existent incident ID
    result_missing = ai_explainer.explain_incident("inc-non-existent-999")
    assert result_missing["has_sufficient_evidence"] is False
    assert "Insufficient evidence to determine a confident root cause." in result_missing["what_happened"]
    assert "Insufficient evidence to determine a confident root cause." in result_missing["likely_root_cause"]

    # 2. Incident with empty/sparse telemetry
    sparse_inc = {
        "id": "inc-sparse-test",
        "incident_id": "inc-sparse-test",
        "title": "Vague Event",
        "severity": "LOW",
        "confidence": 10,
        "root_cause": "Undetermined / Low Confidence",
        "related_event_ids": [],
        "affected_servers": ["server-09"],
        "affected_services": ["worker"]
    }
    db.incidents.insert_one(sparse_inc)
    result_sparse = ai_explainer.explain_incident("inc-sparse-test")
    assert result_sparse["has_sufficient_evidence"] is False
    assert "Insufficient evidence to determine a confident root cause." in result_sparse["what_happened"]

def test_c_security_detector_identifies_repeated_failed_logins():
    """
    Test C: Security detector identifies repeated failed logins and creates security events.
    """
    brute_force_logs = [
        {
            "timestamp": "2026-09-07 14:10:01",
            "server": "server-02",
            "ip": "198.51.100.42",
            "service": "authentication",
            "severity": "WARNING",
            "message": "Failed password for illegal user admin from 198.51.100.42 port 42812 ssh2"
        },
        {
            "timestamp": "2026-09-07 14:10:03",
            "server": "server-02",
            "ip": "198.51.100.42",
            "service": "authentication",
            "severity": "WARNING",
            "message": "pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=198.51.100.42"
        },
        {
            "timestamp": "2026-09-07 14:10:05",
            "server": "server-02",
            "ip": "198.51.100.42",
            "service": "authentication",
            "severity": "WARNING",
            "message": "Failed password for root from 198.51.100.42 port 42814 ssh2"
        }
    ]

    events = security_detector.process_logs(brute_force_logs)
    assert len(events) >= 1
    bf_event = next((e for e in events if e["event_type"] == "Repeated Failed Logins"), None)
    assert bf_event is not None
    assert bf_event["server"] == "server-02"
    assert bf_event["source_ip"] == "198.51.100.42"
    assert bf_event["attempt_count"] >= 3
    assert bf_event["risk_level"] in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]

def test_d_security_detector_identifies_401_403_spikes():
    """
    Test D: Security detector identifies authorization denial spikes (HTTP 401/403).
    """
    auth_denial_logs = [
        {
            "timestamp": "2026-09-07 14:12:00",
            "server": "server-01",
            "ip": "203.0.113.88",
            "service": "web-server",
            "severity": "WARNING",
            "status_code": 401,
            "message": "HTTP 401 Unauthorized: Bearer token missing"
        },
        {
            "timestamp": "2026-09-07 14:12:02",
            "server": "server-01",
            "ip": "203.0.113.88",
            "service": "web-server",
            "severity": "WARNING",
            "status_code": 403,
            "message": "HTTP 403 Forbidden: Client does not have required permissions"
        },
        {
            "timestamp": "2026-09-07 14:12:04",
            "server": "server-01",
            "ip": "203.0.113.88",
            "service": "web-server",
            "severity": "WARNING",
            "status_code": 401,
            "message": "HTTP 401 Unauthorized: Invalid API key"
        }
    ]

    events = security_detector.process_logs(auth_denial_logs)
    assert len(events) >= 1
    spike_event = next((e for e in events if e["event_type"] == "HTTP 401/403 Spike"), None)
    assert spike_event is not None
    assert spike_event["server"] == "server-01"
    assert spike_event["source_ip"] == "203.0.113.88"
    assert spike_event["attempt_count"] >= 3

def test_e_ai_assistant_answers_using_actual_stored_data():
    """
    Test E: AI Assistant answers user questions using actual stored database evidence.
    """
    # 1. Question about Server-03
    ans_srv = ai_assistant.answer_question("Why is Server-03 unhealthy?")
    assert ans_srv["data_found"] is True
    assert ans_srv["related_server"] == "Server-03"
    assert "Server-03" in ans_srv["answer"]
    assert len(ans_srv["key_evidence"]) > 0

    # 2. Question about latest payment failure
    ans_inc = ai_assistant.answer_question("What caused the latest payment failure?")
    assert ans_inc["data_found"] is True
    assert "database" in ans_inc["answer"].lower() or "payment" in ans_inc["answer"].lower()
    assert len(ans_inc["key_evidence"]) > 0

    # 3. Question about security threats
    ans_sec = ai_assistant.answer_question("Are there any security threats in our cloud?")
    assert ans_sec["data_found"] is True
    assert len(ans_sec["key_evidence"]) > 0

def test_f_ai_assistant_handles_questions_with_no_matching_data():
    """
    Test F: AI Assistant handles questions with no matching data without hallucinating.
    """
    # Query for a server that does not exist in cluster
    ans_unknown = ai_assistant.answer_question("Why did Server-99 fail?")
    assert ans_unknown["data_found"] is False
    assert "unavailable" in ans_unknown["answer"].lower() or "not found" in ans_unknown["answer"].lower()

    # Query with no relevance to cloud telemetry
    ans_nonsense = ai_assistant.answer_question("What is the recipe for chocolate cake?")
    assert ans_nonsense["data_found"] is False
    assert "No matching evidence" in ans_nonsense["answer"]
    assert ans_nonsense["confidence_score"] == 0
