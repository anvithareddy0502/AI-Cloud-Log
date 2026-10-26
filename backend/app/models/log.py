from typing import Optional, Dict, Any

class NormalizedLog(dict):
    """
    Standardized internal log dictionary format:
    {
        "id": "log-...",
        "timestamp": "2026-09-07 14:22:04",
        "server": "server-03",
        "service": "payment-api",
        "severity": "ERROR",
        "message": "Database connection timeout",
        "ip": "10.0.2.45",
        "status_code": 500,
        "response_time": 8.7,
        "cpu_usage": 85.0,
        "memory_usage": 72.0,
        "correlation_id": "corr-1234",
        "raw_text": "..."
    }
    """
    pass
