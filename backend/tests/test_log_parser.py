import pytest
from backend.app.services.log_parser import log_parser

def test_parse_csv():
    csv_data = (
        "timestamp,server,service,severity,message,status_code,response_time\n"
        "2026-09-07 14:00:00,server-01,web-server,INFO,Request successful,200,15.5\n"
        "2026-09-07 14:00:05,server-03,database,ERROR,Connection timeout,500,3200.0\n"
    ).encode("utf-8")

    logs, errors = log_parser.parse_file("test.csv", csv_data)
    assert len(logs) == 2
    assert len(errors) == 0
    assert logs[0]["server"] == "server-01"
    assert logs[0]["severity"] == "INFO"
    assert logs[1]["server"] == "server-03"
    assert logs[1]["severity"] == "ERROR"
    assert logs[1]["status_code"] == 500
    assert logs[1]["response_time"] == 3200.0

def test_parse_json():
    json_data = (
        '[{"timestamp": "2026-09-07 14:00:00", "server": "server-02", "service": "authentication", "message": "Failed login", "status_code": 401}]'
    ).encode("utf-8")

    logs, errors = log_parser.parse_file("test.json", json_data)
    assert len(logs) == 1
    assert len(errors) == 0
    assert logs[0]["server"] == "server-02"
    assert logs[0]["status_code"] == 401
    assert logs[0]["severity"] == "WARNING"

def test_parse_text_lines():
    text_data = (
        "2026-09-07 14:00:01 [server-01] [web-server] INFO: GET /healthz 200 OK latency=4.2ms\n"
        "2026-09-07 14:00:02 [server-03] [database] CRITICAL: database unavailable status=500 latency=4500ms\n"
        "malformed line that is just random junk\n"
    ).encode("utf-8")

    logs, errors = log_parser.parse_file("test.log", text_data)
    assert len(logs) == 3
    assert logs[0]["severity"] == "INFO"
    assert logs[1]["severity"] == "CRITICAL"
    assert logs[1]["server"] == "server-03"
