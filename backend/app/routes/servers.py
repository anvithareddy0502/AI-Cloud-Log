from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.database.connection import db
from backend.app.services.health_calculator import health_calculator

router = APIRouter(tags=["Servers"])

@router.get("/servers")
def get_servers():
    """
    Retrieves full inventory of monitored cloud servers with dynamic health scores.
    """
    # Refresh server health scores
    health_calculator.recalculate_all_servers()

    servers = db.servers.find()
    clean_servers = []
    for s in servers:
        clean_servers.append({
            "id": str(s.get("id") or s.get("name", "srv")).lower(),
            "name": s.get("name") or s.get("id", "Server-01"),
            "ip": s.get("ip", "10.0.1.1"),
            "region": s.get("region", "us-east-1a"),
            "status": s.get("status", "Healthy"),
            "health_score": s.get("health_score", 98.0),
            "cpu_usage": s.get("cpu_usage", 25.0),
            "memory_usage": s.get("memory_usage", 45.0),
            "disk_usage": s.get("disk_usage", 30.0),
            "active_services": s.get("active_services", ["Web Server"]),
            "last_ping": s.get("last_ping", "1s ago")
        })
    return clean_servers

@router.get("/servers/{server_id}")
def get_server_by_id(server_id: str):
    """
    Retrieves detailed health calculation breakdown and telemetry for a specific server.
    """
    srv_lower = server_id.lower()
    srv = db.servers.find_one({"id": srv_lower}) or db.servers.find_one({"name": server_id})
    if not srv:
        raise HTTPException(status_code=404, detail="Server not found in cluster inventory")

    health_detail = health_calculator.calculate_server_health(srv_lower)
    return {
        "server": srv,
        "health_assessment": health_detail
    }
