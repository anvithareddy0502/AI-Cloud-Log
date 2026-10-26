from typing import List, Optional
from pydantic import BaseModel

class ServerResponse(BaseModel):
    id: str
    name: str
    ip: str
    region: str
    status: str  # Healthy, Warning, Critical
    health_score: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_services: List[str]
    last_ping: str

class ServerHealthSummary(BaseModel):
    total_servers: int
    healthy_count: int
    warning_count: int
    critical_count: int
    health_percentage: float
