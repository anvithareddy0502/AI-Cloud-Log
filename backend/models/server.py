from typing import List, Optional
from pydantic import BaseModel

class CloudServer(BaseModel):
    id: str
    name: str
    ip: str
    region: str
    status: str  # healthy, warning, critical
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_services: List[str]
    last_ping: str

class CloudHealthOverview(BaseModel):
    total_servers: int
    healthy_count: int
    warning_count: int
    critical_count: int
    health_percentage: float
