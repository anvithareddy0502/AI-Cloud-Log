from typing import Dict, Any, List
from backend.app.database.connection import db
from backend.app.utils.logger import logger

class HealthCalculatorService:
    """
    Transparent, deterministic server health calculation service.
    Computes health scores between 0 and 100 and classifies nodes as Healthy, Warning, or Critical.
    """

    def calculate_server_health(self, server_id: str) -> Dict[str, Any]:
        """
        Calculates health metrics for a specific server node based on actual database logs and anomalies.
        """
        srv_name = server_id.lower()

        # 1. Fetch server logs
        logs = db.logs.find({"server": srv_name}, limit=200)
        # 2. Fetch server anomalies
        anomalies = db.anomalies.find({"server": srv_name, "status": "Active"})

        total_logs = len(logs)
        if total_logs == 0:
            # Fallback to server's existing score or optimal 100
            existing = db.servers.find_one({"id": srv_name}) or db.servers.find_one({"name": srv_name})
            return {
                "server_id": srv_name,
                "health_score": existing.get("health_score", 98.0) if existing else 98.0,
                "status": existing.get("status", "Healthy") if existing else "Healthy",
                "factors": {"message": "No recent events to evaluate"}
            }

        critical_count = sum(1 for l in logs if str(l.get("severity", "")).upper() == "CRITICAL")
        error_count = sum(1 for l in logs if str(l.get("severity", "")).upper() == "ERROR")
        warning_count = sum(1 for l in logs if str(l.get("severity", "")).upper() == "WARNING")
        http_5xx_count = sum(1 for l in logs if l.get("status_code") and 500 <= int(l.get("status_code")) < 600)
        anomaly_count = len(anomalies)

        rts = [float(l["response_time"]) for l in logs if l.get("response_time") is not None]
        avg_rt = sum(rts) / len(rts) if rts else 25.0

        error_rate = (error_count + critical_count) / total_logs

        # Deterministic deduction breakdown
        error_penalty = min(round(error_rate * 50.0, 1), 35.0)
        critical_penalty = min(critical_count * 12.0, 30.0)
        anomaly_penalty = min(anomaly_count * 10.0, 25.0)
        http_5xx_penalty = min(http_5xx_count * 4.0, 20.0)

        latency_penalty = 0.0
        if avg_rt > 1500.0:
            latency_penalty = 15.0
        elif avg_rt > 500.0:
            latency_penalty = 8.0

        raw_score = 100.0 - (error_penalty + critical_penalty + anomaly_penalty + http_5xx_penalty + latency_penalty)
        score = max(0.0, min(100.0, round(raw_score, 1)))

        # Classification
        if score >= 80.0:
            status = "Healthy"
        elif score >= 60.0:
            status = "Warning"
        else:
            status = "Critical"

        # Update in database
        db.servers.update_one(
            {"id": srv_name},
            {"$set": {
                "health_score": score,
                "status": status,
                "last_calculated": "just now"
            }},
            upsert=False
        )

        return {
            "server_id": srv_name,
            "health_score": score,
            "status": status,
            "factors": {
                "total_logs": total_logs,
                "error_rate": round(error_rate, 4),
                "critical_count": critical_count,
                "error_count": error_count,
                "anomaly_count": anomaly_count,
                "http_5xx_count": http_5xx_count,
                "avg_response_time": round(avg_rt, 1),
                "deductions": {
                    "error_penalty": error_penalty,
                    "critical_penalty": critical_penalty,
                    "anomaly_penalty": anomaly_penalty,
                    "http_5xx_penalty": http_5xx_penalty,
                    "latency_penalty": latency_penalty
                }
            }
        }

    def recalculate_all_servers(self) -> Dict[str, Any]:
        """
        Recalculates health scores for all servers in the cluster and returns summary statistics.
        """
        servers = db.servers.find()
        for srv in servers:
            sid = srv.get("id") or srv.get("name")
            if sid:
                self.calculate_server_health(str(sid))

        updated_servers = db.servers.find()
        total = len(updated_servers)
        healthy = sum(1 for s in updated_servers if str(s.get("status", "")).lower() == "healthy")
        warning = sum(1 for s in updated_servers if str(s.get("status", "")).lower() == "warning")
        critical = sum(1 for s in updated_servers if str(s.get("status", "")).lower() == "critical")
        pct = round((healthy / total) * 100, 1) if total > 0 else 100.0

        return {
            "total_servers": total,
            "healthy_count": healthy,
            "warning_count": warning,
            "critical_count": critical,
            "health_percentage": pct
        }

health_calculator = HealthCalculatorService()
