class AnomalyModel(dict):
    """
    Internal anomaly representation:
    {
        "id": "anom-...",
        "server": "server-03",
        "service": "payment-api",
        "time_window": "2026-09-07 14:20:00 - 14:25:00",
        "detection_time": "2 min ago",
        "anomaly_score": 0.91,
        "severity": "HIGH",
        "reason": "Unusual increase in database errors and HTTP 5xx responses",
        "status": "OPEN",
        "features": {...}
    }
    """
    pass
