from typing import List, Optional

class ServerModel(dict):
    """
    Internal server representation:
    {
        "id": "server-03",
        "name": "Server-03",
        "ip": "10.0.2.45",
        "region": "us-east-1c",
        "status": "Critical",  # Healthy, Warning, Critical
        "health_score": 42.5,
        "cpu_usage": 96.8,
        "memory_usage": 91.2,
        "disk_usage": 79.4,
        "active_services": ["database", "payment-api"],
        "last_ping": "just now"
    }
    """
    pass
