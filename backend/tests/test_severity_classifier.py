import pytest
from backend.app.services.log_classifier import log_classifier

def test_explicit_severity_preserved():
    assert log_classifier.classify("all systems operational", explicit_severity="CRITICAL") == "CRITICAL"
    assert log_classifier.classify("fatal crash detected", explicit_severity="INFO") == "INFO"
    assert log_classifier.classify("timeout happened", explicit_severity="WARNING") == "WARNING"

def test_inferred_critical():
    assert log_classifier.classify("fatal: database unavailable and connection slots are reserved") == "CRITICAL"
    assert log_classifier.classify("multiple authentication failures detected from external IP") == "CRITICAL"
    assert log_classifier.classify("kernel panic system crash") == "CRITICAL"

def test_inferred_error():
    assert log_classifier.classify("HTTP 500 internal error on payment process") == "ERROR"
    assert log_classifier.classify("connection refused by upstream target host") == "ERROR"
    assert log_classifier.classify("operation timed out after 30000ms") == "ERROR"

def test_inferred_warning():
    assert log_classifier.classify("high usage of memory pool: 92% capacity") == "WARNING"
    assert log_classifier.classify("slow query detected taking 2400ms") == "WARNING"
    assert log_classifier.classify("retry attempt 3 of 5") == "WARNING"

def test_inferred_info():
    assert log_classifier.classify("service started and initialized on port 8080") == "INFO"
    assert log_classifier.classify("connection completed successfully") == "INFO"
    assert log_classifier.classify("routine health check heartbeat acknowledged") == "INFO"
