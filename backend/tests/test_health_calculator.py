import pytest
from backend.app.services.health_calculator import health_calculator
from backend.app.database.connection import db

def test_health_calculation_ranges():
    # Insert temporary healthy server logs
    test_server = "server-test-health"
    db.servers.insert_one({"id": test_server, "name": "Server-Test", "health_score": 100.0, "status": "Healthy"})

    # Clean logs: health score should be high (>= 80, Healthy)
    db.logs.insert_many([
        {"server": test_server, "severity": "INFO", "response_time": 20.0},
        {"server": test_server, "severity": "INFO", "response_time": 25.0}
    ])
    res = health_calculator.calculate_server_health(test_server)
    assert res["health_score"] >= 80.0
    assert res["status"] == "Healthy"

    # Add critical errors and 5xx logs: health score should degrade
    db.logs.insert_many([
        {"server": test_server, "severity": "CRITICAL", "status_code": 500, "response_time": 3500.0},
        {"server": test_server, "severity": "CRITICAL", "status_code": 500, "response_time": 4000.0},
        {"server": test_server, "severity": "ERROR", "status_code": 500, "response_time": 3000.0},
        {"server": test_server, "severity": "ERROR", "status_code": 500, "response_time": 3000.0}
    ])
    res_degraded = health_calculator.calculate_server_health(test_server)
    assert res_degraded["health_score"] < 80.0
    assert res_degraded["status"] in {"Warning", "Critical"}

    # Cleanup
    db.servers.delete_many({"id": test_server})
    db.logs.delete_many({"server": test_server})
