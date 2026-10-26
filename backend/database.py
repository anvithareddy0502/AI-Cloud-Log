import logging
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.data.mock_data import (
    SERVERS, INCIDENTS, ANOMALIES, SECURITY_EVENTS, MOCK_LOGS,
    REPORTS, ACTIVITY_CHART_DATA, ERROR_TREND_DATA, ASSISTANT_KNOWLEDGE
)

logger = logging.getLogger("aiclar.database")

class DatabaseManager:
    def __init__(self):
        self.is_connected_to_mongo = False
        self.client = None
        self.db = None
        
        # In-memory stores initialized from rich mock data
        self.logs: List[Dict[str, Any]] = list(MOCK_LOGS)
        self.incidents: List[Dict[str, Any]] = list(INCIDENTS)
        self.anomalies: List[Dict[str, Any]] = list(ANOMALIES)
        self.security_events: List[Dict[str, Any]] = list(SECURITY_EVENTS)
        self.servers: List[Dict[str, Any]] = list(SERVERS)
        self.reports: List[Dict[str, Any]] = list(REPORTS)
        
    def connect(self):
        """Attempt MongoDB connection; fall back smoothly to memory store if unavailable."""
        try:
            from pymongo import MongoClient
            self.client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=1000)
            # Trigger quick server ping
            self.client.admin.command('ping')
            self.db = self.client[settings.DATABASE_NAME]
            self.is_connected_to_mongo = True
            logger.info("Successfully connected to live MongoDB instance at %s", settings.MONGODB_URI)
        except Exception as e:
            self.is_connected_to_mongo = False
            logger.warning(
                "MongoDB not available (%s). Seamlessly operating with AI-CLAR resilient In-Memory Repository.",
                str(e)
            )

    # -------------------------------------------------------------
    # LOGS REPOSITORY
    # -------------------------------------------------------------
    def get_logs(
        self,
        server: Optional[str] = None,
        service: Optional[str] = None,
        severity: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> Dict[str, Any]:
        filtered = self.logs
        if server and server.lower() != "all":
            filtered = [l for l in filtered if l["server"].lower() == server.lower()]
        if service and service.lower() != "all":
            filtered = [l for l in filtered if l["service"].lower() == service.lower()]
        if severity and severity.lower() != "all":
            filtered = [l for l in filtered if l["severity"].lower() == severity.lower()]
        if search:
            q = search.lower()
            filtered = [
                l for l in filtered
                if q in l["message"].lower() or q in l["server"].lower() or q in l.get("correlation_id", "").lower()
            ]
            
        total = len(filtered)
        paginated = filtered[skip : skip + limit]
        return {
            "total": total,
            "count": len(paginated),
            "limit": limit,
            "skip": skip,
            "logs": paginated
        }

    def get_log_by_id(self, log_id: str) -> Optional[Dict[str, Any]]:
        for log in self.logs:
            if log["id"] == log_id:
                return log
        return None

    # -------------------------------------------------------------
    # INCIDENTS REPOSITORY
    # -------------------------------------------------------------
    def get_incidents(self) -> List[Dict[str, Any]]:
        return self.incidents

    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        for inc in self.incidents:
            if inc["id"] == incident_id:
                return inc
        return None

    # -------------------------------------------------------------
    # ANOMALIES REPOSITORY
    # -------------------------------------------------------------
    def get_anomalies(self) -> List[Dict[str, Any]]:
        return self.anomalies

    # -------------------------------------------------------------
    # SECURITY REPOSITORY
    # -------------------------------------------------------------
    def get_security_events(self) -> List[Dict[str, Any]]:
        return self.security_events

    # -------------------------------------------------------------
    # SERVERS REPOSITORY
    # -------------------------------------------------------------
    def get_servers(self) -> List[Dict[str, Any]]:
        return self.servers

    def get_server_health_summary(self) -> Dict[str, Any]:
        healthy = sum(1 for s in self.servers if s["status"] == "healthy")
        warning = sum(1 for s in self.servers if s["status"] == "warning")
        critical = sum(1 for s in self.servers if s["status"] == "critical")
        total = len(self.servers)
        pct = round((healthy / total) * 100, 1) if total > 0 else 100.0
        return {
            "total_servers": total,
            "healthy_count": healthy,
            "warning_count": warning,
            "critical_count": critical,
            "health_percentage": pct
        }

    # -------------------------------------------------------------
    # DASHBOARD STATS REPOSITORY
    # -------------------------------------------------------------
    def get_dashboard_stats(self) -> Dict[str, Any]:
        health = self.get_server_health_summary()
        active_incidents = sum(1 for inc in self.incidents if inc["status"] != "Resolved")
        anomalies_detected = len(self.anomalies)
        critical_errors = sum(1 for log in self.logs if log["severity"] == "CRITICAL")
        
        return {
            "kpis": {
                "cloud_health_pct": health["health_percentage"],
                "active_incidents": active_incidents,
                "anomalies_detected": anomalies_detected,
                "critical_errors": critical_errors
            },
            "server_health": health,
            "prominent_incident": self.incidents[0] if self.incidents else None,
            "activity_chart": ACTIVITY_CHART_DATA,
            "error_trend_chart": ERROR_TREND_DATA,
            "recent_incidents": self.incidents[:5]
        }

    # -------------------------------------------------------------
    # REPORTS REPOSITORY
    # -------------------------------------------------------------
    def get_reports(self) -> List[Dict[str, Any]]:
        return self.reports

    def add_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        self.reports.insert(0, report)
        return report

# Global DB singleton instance
db_manager = DatabaseManager()
