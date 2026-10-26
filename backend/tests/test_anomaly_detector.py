import pytest
from backend.app.ml.anomaly_model import anomaly_model

def test_normal_telemetry_not_anomaly():
    normal_features = {
        "server": "server-01",
        "error_count": 0,
        "warning_count": 1,
        "events_per_minute": 20.0,
        "error_rate": 0.0,
        "average_response_time": 25.0,
        "HTTP_5xx_count": 0,
        "failed_login_count": 0
    }
    res = anomaly_model.evaluate_window(normal_features)
    assert res["is_anomaly"] is False
    assert res["anomaly_score"] < 0.60

def test_severe_database_outage_flagged():
    outage_features = {
        "server": "server-03",
        "error_count": 25,
        "critical_count": 8,
        "warning_count": 12,
        "events_per_minute": 60.0,
        "error_rate": 0.55,
        "average_response_time": 4200.0,
        "HTTP_5xx_count": 25,
        "failed_login_count": 0
    }
    res = anomaly_model.evaluate_window(outage_features)
    assert res["is_anomaly"] is True
    assert res["anomaly_score"] >= 0.85
    assert res["severity"] == "HIGH"
    assert "critical" in res["reason"].lower() or "5xx" in res["reason"].lower()

def test_auth_brute_force_flagged():
    auth_features = {
        "server": "server-02",
        "error_count": 10,
        "critical_count": 2,
        "warning_count": 5,
        "events_per_minute": 15.0,
        "error_rate": 0.80,
        "average_response_time": 120.0,
        "HTTP_5xx_count": 0,
        "failed_login_count": 47
    }
    res = anomaly_model.evaluate_window(auth_features)
    assert res["is_anomaly"] is True
    assert res["severity"] == "HIGH"
    assert "failed login" in res["reason"].lower() or "auth" in res["reason"].lower()
