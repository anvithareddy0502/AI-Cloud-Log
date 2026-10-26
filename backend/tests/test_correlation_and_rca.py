import pytest
from backend.app.services.event_correlator import event_correlator
from backend.app.services.root_cause_engine import root_cause_engine
from backend.app.models.incident import IncidentStatus
from backend.app.database.connection import db

def test_a_normal_logs_do_not_trigger_incidents():
    """
    Test A: Normal unrelated logs do not trigger incidents.
    INFO logs without errors or warnings must yield 0 incident clusters.
    """
    normal_logs = [
        {
            "timestamp": "2026-09-07 14:00:01",
            "server": "server-01",
            "service": "web-server",
            "severity": "INFO",
            "message": "GET /api/v1/products HTTP/1.1 200 OK",
            "status_code": 200,
            "response_time": 45
        },
        {
            "timestamp": "2026-09-07 14:00:05",
            "server": "server-02",
            "service": "authentication",
            "severity": "INFO",
            "message": "User session validated successfully for user_id=4821",
            "status_code": 200
        },
        {
            "timestamp": "2026-09-07 14:00:10",
            "server": "server-03",
            "service": "database",
            "severity": "INFO",
            "message": "SELECT * FROM orders WHERE id=9928 executed in 4ms"
        }
    ]
    clusters = event_correlator.cluster_events(normal_logs)
    assert len(clusters) == 0, f"Expected 0 incident clusters for normal logs, got {len(clusters)}"

def test_b_database_failure_and_api_errors_grouped():
    """
    Test B: Database failure + API errors are grouped into a single incident.
    Verifies service dependency traversal: database -> payment-api -> web-server.
    """
    cascade_logs = [
        {
            "id": "log-db-1",
            "timestamp": "2026-09-07 14:15:00",
            "server": "server-03",
            "service": "database",
            "severity": "CRITICAL",
            "message": "psql: fatal: remaining connection slots are reserved for non-replication superuser connections"
        },
        {
            "id": "log-api-1",
            "timestamp": "2026-09-07 14:15:35",
            "server": "server-04",
            "service": "payment-api",
            "severity": "ERROR",
            "message": "HTTP 504 Gateway Timeout: failed to acquire connection from HikariCP database pool within 30000ms",
            "status_code": 504,
            "response_time": 30000
        },
        {
            "id": "log-web-1",
            "timestamp": "2026-09-07 14:16:10",
            "server": "server-01",
            "service": "web-server",
            "severity": "ERROR",
            "message": "Upstream service payment-api returned 504 on POST /checkout",
            "status_code": 504
        }
    ]
    clusters = event_correlator.cluster_events(cascade_logs)
    assert len(clusters) == 1, f"Expected 1 correlated incident cluster, got {len(clusters)}"
    cluster = clusters[0]
    servers = set(e["server"] for e in cluster)
    services = set(e["service"] for e in cluster)
    assert "server-03" in servers and "server-04" in servers
    assert "database" in services and "payment-api" in services

def test_c_separate_errors_on_unrelated_servers_remain_separate():
    """
    Test C: Separate errors on unrelated servers create separate incidents.
    Unrelated server errors without causal links must generate separate clusters.
    """
    unrelated_logs = [
        {
            "id": "log-auth-fail",
            "timestamp": "2026-09-07 14:20:00",
            "server": "server-02",
            "service": "authentication",
            "severity": "ERROR",
            "message": "PAM authentication failure for illegal user admin from 198.51.100.42"
        },
        {
            "id": "log-disk-full",
            "timestamp": "2026-09-07 14:20:15",
            "server": "server-05",
            "service": "cache",
            "severity": "ERROR",
            "message": "OOM command not allowed when used memory > 'maxmemory'"
        }
    ]
    clusters = event_correlator.cluster_events(unrelated_logs)
    assert len(clusters) == 2, f"Expected 2 separate incident clusters for unrelated servers, got {len(clusters)}"

def test_d_cpu_warning_and_app_error_on_same_server_correlate():
    """
    Test D: High CPU warning + app error on same server correlate properly.
    Verifies server locality correlation within the sliding time window.
    """
    same_server_logs = [
        {
            "id": "log-cpu-warn",
            "timestamp": "2026-09-07 14:30:00",
            "server": "server-01",
            "service": "web-server",
            "severity": "WARNING",
            "cpu_usage": 92.5,
            "message": "CPU load exceeded warning threshold: 92.5%"
        },
        {
            "id": "log-worker-crash",
            "timestamp": "2026-09-07 14:30:40",
            "server": "server-01",
            "service": "web-server",
            "severity": "ERROR",
            "message": "Worker process 4819 terminated unexpectedly due to CPU throttling"
        }
    ]
    clusters = event_correlator.cluster_events(same_server_logs)
    assert len(clusters) == 1, f"Expected 1 correlated cluster for same-server events, got {len(clusters)}"
    assert clusters[0][0]["server"] == "server-01"

def test_e_root_cause_engine_confidence_and_hierarchy():
    """
    Test E: Root cause engine gives higher confidence to earlier root events
    in a dependency chain vs downstream symptoms.
    """
    # Cascade with root cause at database
    full_cascade = [
        {
            "timestamp": "2026-09-07 14:00:00",
            "server": "server-03",
            "service": "database",
            "severity": "CRITICAL",
            "message": "psql: fatal: remaining connection slots are reserved",
            "anomaly_score": 0.95
        },
        {
            "timestamp": "2026-09-07 14:00:30",
            "server": "server-04",
            "service": "payment-api",
            "severity": "ERROR",
            "message": "HTTP 504 Gateway Timeout: database connection pool timeout",
            "anomaly_score": 0.85
        },
        {
            "timestamp": "2026-09-07 14:01:00",
            "server": "server-01",
            "service": "web-server",
            "severity": "ERROR",
            "message": "HTTP 500 Internal Server Error in payment checkout proxy",
            "anomaly_score": 0.80
        }
    ]
    rca_full = root_cause_engine.analyze(full_cascade)

    # Downstream symptom only
    downstream_only = [
        {
            "timestamp": "2026-09-07 14:01:00",
            "server": "server-01",
            "service": "web-server",
            "severity": "ERROR",
            "message": "HTTP 500 Internal Server Error in payment checkout proxy"
        }
    ]
    rca_downstream = root_cause_engine.analyze(downstream_only)

    # Database was identified as the root cause service
    assert rca_full["primary_service"] == "database"
    assert "database" in rca_full["root_cause"].lower() or "connection" in rca_full["root_cause"].lower()
    
    # Confidence in root cause with verified cascade is higher than isolated downstream symptom
    assert rca_full["confidence"] > rca_downstream["confidence"]
    assert rca_full["confidence"] >= 80

def test_rca_weak_evidence_fallback():
    """
    Verifies that sparse/ambiguous evidence produces an explicit low-confidence result.
    """
    ambiguous_logs = [
        {
            "timestamp": "2026-09-07 14:50:00",
            "server": "server-06",
            "service": "analytics",
            "severity": "WARNING",
            "message": "Minor jitter in background sync queue"
        }
    ]
    rca = root_cause_engine.analyze(ambiguous_logs)
    assert rca["confidence"] < 40
    assert "low confidence" in rca["root_cause"].lower() or "undetermined" in rca["root_cause"].lower()
    assert len(rca["evidence"]) > 0

def test_incident_lifecycle_resolve_and_ignore():
    """
    Verifies the incident creation and status lifecycle (OPEN/INVESTIGATING -> RESOLVED / IGNORED).
    """
    from backend.app.routes.incidents import (
        resolve_incident,
        ignore_incident,
        get_incident_by_id,
        update_incident_status
    )
    from backend.app.schemas.incident import IncidentStatusUpdate

    # Test logs that trigger an incident
    incident_logs = [
        {
            "id": "log-test-1",
            "timestamp": "2026-09-07 15:00:00",
            "server": "server-08",
            "service": "order-service",
            "severity": "CRITICAL",
            "message": "Order service panic: unhandled exception in checkout handler"
        }
    ]
    created = event_correlator.correlate_and_create_incidents(incident_logs)
    assert len(created) >= 1
    inc_id = created[0]["id"]

    # Verify initial retrieval
    inc = get_incident_by_id(inc_id)
    assert inc["status"] in [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]

    # Resolve incident
    res_resp = resolve_incident(inc_id)
    assert res_resp["incident"]["status"] == IncidentStatus.RESOLVED

    # Re-fetch and assert persistent status
    inc_after_res = get_incident_by_id(inc_id)
    assert inc_after_res["status"] == IncidentStatus.RESOLVED

    # Ignore incident
    ign_resp = ignore_incident(inc_id)
    assert ign_resp["incident"]["status"] == IncidentStatus.IGNORED

    # Status update via generic endpoint
    update_incident_status(inc_id, IncidentStatusUpdate(status="INVESTIGATING"))
    inc_after_inv = get_incident_by_id(inc_id)
    assert inc_after_inv["status"] == IncidentStatus.INVESTIGATING
