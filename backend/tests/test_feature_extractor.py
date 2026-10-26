import pytest
from backend.app.services.feature_extractor import feature_extractor

def test_feature_extraction_metrics():
    logs = [
        {"timestamp": "2026-09-07 14:00:01", "server": "server-03", "service": "database", "severity": "CRITICAL", "status_code": 500, "response_time": 3000.0, "message": "DB timeout"},
        {"timestamp": "2026-09-07 14:00:05", "server": "server-03", "service": "database", "severity": "ERROR", "status_code": 500, "response_time": 2500.0, "message": "connection failed"},
        {"timestamp": "2026-09-07 14:00:10", "server": "server-03", "service": "database", "severity": "WARNING", "status_code": 200, "response_time": 100.0, "message": "slow query"},
        {"timestamp": "2026-09-07 14:00:15", "server": "server-03", "service": "database", "severity": "INFO", "status_code": 200, "response_time": 20.0, "message": "ping"}
    ]

    features = feature_extractor.extract_features(logs)
    assert len(features) == 1
    f = features[0]
    assert f["server"] == "server-03"
    assert f["total_events"] == 4
    assert f["critical_count"] == 1
    assert f["error_count"] == 1
    assert f["warning_count"] == 1
    assert f["info_count"] == 1
    assert f["error_rate"] == 0.5
    assert f["HTTP_5xx_count"] == 2
    assert f["average_response_time"] == round((3000.0 + 2500.0 + 100.0 + 20.0) / 4, 2)
