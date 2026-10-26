"""
AI-CLAR Remediation Recommendation Engine
Extension Point for Phase 2:
- Suggests runbook mitigation steps based on incident classification.
"""
from typing import List

class RecommendationEngineService:
    def get_recommendations_for_cause(self, root_cause: str) -> List[str]:
        rc = root_cause.lower()
        if "database" in rc or "connection" in rc:
            return [
                "Check database availability and connection pool limits",
                "Execute 'SELECT * FROM pg_stat_activity' to identify long-running transactions",
                "Increase max_connections or adjust pgbouncer pool sizing",
                "Review recent database migrations deployed to Server-03"
            ]
        elif "login" in rc or "brute" in rc or "auth" in rc:
            return [
                "Block malicious ingress IP address at edge security group",
                "Enforce multi-factor authentication (MFA) on elevated accounts",
                "Verify fail2ban / rate-limiting configurations",
                "Audit PAM authentication logs for lateral movement"
            ]
        elif "cpu" in rc or "memory" in rc:
            return [
                "Inspect worker thread allocation and process status",
                "Deploy hotfix for high-complexity compute or regex loops",
                "Trigger horizontal auto-scaling pod replica increment",
                "Clear temporary worker caches"
            ]
        return [
            "Inspect system health logs and service status",
            "Verify network reachability and latency metrics",
            "Review deployment commit history for recent rollouts"
        ]

recommender = RecommendationEngineService()
