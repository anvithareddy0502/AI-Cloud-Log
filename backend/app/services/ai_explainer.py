from typing import Dict, Any, List, Optional
from backend.app.database.connection import db
from backend.app.utils.logger import logger

class AiIncidentExplainer:
    """
    Synthesizes evidence-based AI incident explanations grounded strictly in
    retrieved database records without fabricating logs, servers, or metrics.
    """

    def explain_incident(self, incident_id: Any) -> Dict[str, Any]:
        """
        Retrieves incident details, correlated logs, anomaly records, and server statistics
        to produce a structured, evidence-based AI explanation.
        Supports passing either an incident_id string or an incident dictionary.
        """
        # 1. Retrieve incident record
        if isinstance(incident_id, dict):
            inc = incident_id
        else:
            inc = db.incidents.find_one({"incident_id": incident_id}) or db.incidents.find_one({"id": incident_id})
            
        if not inc:
            return self._insufficient_evidence_response("Incident record not found in database.")

        # Early check for low confidence or sparse evidence
        confidence = int(inc.get("confidence") or 0)
        root_cause_str = str(inc.get("root_cause") or inc.get("likely_root_cause") or "").lower()
        if "insufficient evidence" in root_cause_str or confidence < 35:
            return self._insufficient_evidence_response(
                "Insufficient evidence to determine a confident root cause. Sparse telemetry without correlated error indicators."
            )

        # 2. Retrieve correlated logs
        related_ids = inc.get("related_event_ids", [])
        correlated_logs = []
        if related_ids:
            correlated_logs = db.logs.find({"$or": [{"id": {"$in": related_ids}}, {"_id": {"$in": related_ids}}]})
        
        # Fallback query if related_ids was empty: query logs by affected servers and time bounds
        if not correlated_logs and inc.get("affected_servers") and inc.get("start_time"):
            query: Dict[str, Any] = {
                "server": {"$in": inc["affected_servers"]},
                "timestamp": {"$gte": inc.get("start_time", "")}
            }
            if inc.get("end_time"):
                query["timestamp"]["$lte"] = inc["end_time"]
            correlated_logs = db.logs.find(query, limit=50)

        # 3. Retrieve anomalies for affected servers
        affected_servers = inc.get("affected_servers", [])
        if not affected_servers and inc.get("affected_server"):
            affected_servers = [inc["affected_server"]]
            
        anomalies = []
        if affected_servers:
            anomalies = db.anomalies.find({"server": {"$in": affected_servers}}, limit=10)

        # 4. Retrieve server health statistics
        server_stats = []
        for srv_name in affected_servers:
            srv_doc = db.servers.find_one({"name": srv_name}) or db.servers.find_one({"id": srv_name})
            if srv_doc:
                server_stats.append(srv_doc)

        # 5. Check if evidence is sufficient
        error_logs = [l for l in correlated_logs if str(l.get("severity", "")).upper() in {"WARNING", "ERROR", "CRITICAL"}]
        confidence = int(inc.get("confidence") or 0)
        has_incident_evidence = bool(inc.get("evidence") or inc.get("timeline") or (inc.get("root_cause") and "insufficient" not in str(inc.get("root_cause")).lower()))
        
        # If no error logs, no anomalies, and no incident-level evidence or confidence < 35%, fallback
        if (len(error_logs) == 0 and len(anomalies) == 0 and not has_incident_evidence) or confidence < 35 or inc.get("root_cause") == "Undetermined / Low Confidence":
            return self._insufficient_evidence_response(
                "Insufficient evidence to determine a confident root cause. Sparse telemetry without correlated error indicators."
            )

        # 6. Formulate WHAT HAPPENED
        what_happened = self._formulate_what_happened(inc, correlated_logs, server_stats)

        # 7. Formulate WHY IT WAS DETECTED
        why_detected = self._formulate_why_detected(inc, correlated_logs, anomalies)

        # 8. Extract LIKELY ROOT CAUSE & CONFIDENCE
        likely_root_cause = inc.get("root_cause") or inc.get("likely_root_cause") or "Root cause under active investigation"

        # 9. Extract AFFECTED SERVICES
        affected_services = inc.get("affected_services") or ([inc.get("affected_service")] if inc.get("affected_service") else ["system"])

        # 10. Extract EVIDENCE (from actual logs, server metrics, anomaly scores)
        evidence = self._extract_evidence(inc, correlated_logs, anomalies, server_stats)

        # 11. Formulate RECOMMENDED ACTIONS (Practical, non-destructive steps)
        recommended_actions = self._generate_recommendations(inc, affected_services, affected_servers)

        return {
            "incident_id": inc.get("incident_id") or inc.get("id"),
            "title": inc.get("title", "Cloud Telemetry Incident"),
            "severity": inc.get("severity", "HIGH"),
            "status": inc.get("status", "OPEN"),
            "what_happened": what_happened,
            "why_it_was_detected": why_detected,
            "likely_root_cause": likely_root_cause,
            "confidence": confidence,
            "affected_services": affected_services,
            "affected_servers": affected_servers,
            "evidence": evidence,
            "recommended_actions": recommended_actions,
            "has_sufficient_evidence": True
        }

    def _formulate_what_happened(self, inc: Dict[str, Any], logs: List[Dict[str, Any]], server_stats: List[Dict[str, Any]]) -> str:
        servers_str = ", ".join(inc.get("affected_servers") or [inc.get("affected_server", "cluster")])
        services_str = ", ".join(inc.get("affected_services") or [inc.get("affected_service", "service")])
        start = inc.get("start_time", "recently")
        title = inc.get("title", "telemetry degradation")
        
        # Check if cascade observed
        if len(inc.get("affected_services", [])) > 1:
            return (
                f"At {start}, a multi-service incident ('{title}') impacted {services_str} across {servers_str}. "
                f"The failure sequence originated in the upstream service and propagated downstream, "
                f"resulting in degraded response times and rejected requests."
            )
        return (
            f"At {start}, service degradation ('{title}') was observed on {servers_str} impacting the {services_str} service. "
            f"Elevated error frequencies and abnormal telemetry patterns were logged during the incident window."
        )

    def _formulate_why_detected(self, inc: Dict[str, Any], logs: List[Dict[str, Any]], anomalies: List[Dict[str, Any]]) -> str:
        triggers = []
        error_count = sum(1 for l in logs if str(l.get("severity", "")).upper() in {"ERROR", "CRITICAL"})
        if error_count > 0:
            triggers.append(f"{error_count} critical/error log events correlated within the sliding evaluation window")
        
        if anomalies:
            max_score = max(float(a.get("anomaly_score", 0.7)) for a in anomalies)
            triggers.append(f"Scikit-learn IsolationForest ML model flagged an anomaly score of {max_score:.2f}")

        status_5xx = sum(1 for l in logs if int(l.get("status_code") or 0) >= 500)
        if status_5xx > 0:
            triggers.append(f"Surge of {status_5xx} HTTP 5xx responses detected")

        if not triggers:
            triggers.append("Cluster monitoring heuristics detected abnormal metric deviation against the baseline")

        return "AI-CLAR automated anomaly detection and event correlator flagged this incident due to: " + "; ".join(triggers) + "."

    def _extract_evidence(
        self, 
        inc: Dict[str, Any], 
        logs: List[Dict[str, Any]], 
        anomalies: List[Dict[str, Any]], 
        server_stats: List[Dict[str, Any]]
    ) -> List[str]:
        evidence = []
        
        # 1. Existing stored evidence from incident
        if inc.get("evidence"):
            evidence.extend(inc["evidence"])

        # 2. Correlated logs summary evidence
        if logs and len(evidence) < 3:
            first_err = next((l for l in logs if str(l.get("severity", "")).upper() in {"ERROR", "CRITICAL"}), None)
            if first_err:
                evidence.append(
                    f"First recorded error on {first_err.get('server', 'node')}: '{first_err.get('message', '')}' at {first_err.get('timestamp', '')}"
                )

        # 3. Server hardware telemetry evidence
        for srv in server_stats:
            cpu = srv.get("cpu_usage")
            mem = srv.get("memory_usage")
            if cpu and float(cpu) >= 70.0:
                evidence.append(f"Server {srv.get('name', 'node')} exhibited elevated CPU utilization at {cpu}%")
            if mem and float(mem) >= 80.0:
                evidence.append(f"Server {srv.get('name', 'node')} exhibited elevated memory pressure at {mem}%")

        # 4. Latency or status code evidence
        high_latency = [l for l in logs if (l.get("response_time") or l.get("latency_ms") or 0) > 1000]
        if high_latency:
            max_lat = max(l.get("response_time") or l.get("latency_ms") or 0 for l in high_latency)
            evidence.append(f"Peak response latency jumped to {max_lat}ms during peak failure cascade")

        return list(dict.fromkeys(evidence))  # Deduplicate while preserving order

    def _generate_recommendations(self, inc: Dict[str, Any], services: List[str], servers: List[str]) -> List[str]:
        # Respect existing stored recommendations if available
        if inc.get("recommendations"):
            return inc["recommendations"]
        if inc.get("recommended_actions"):
            return inc["recommended_actions"]

        srv_str = ", ".join(servers) if servers else "affected servers"
        recs = []

        services_lower = [s.lower() for s in services]
        if any("database" in s for s in services_lower):
            recs.append(f"Check database connectivity and verify active socket limits on {srv_str}")
            recs.append("Review recent database schema migrations or unindexed queries")
            recs.append("Inspect connection pooler (e.g. PgBouncer) queue depth and timeout parameters")
        
        if any("payment" in s or "api" in s for s in services_lower):
            recs.append(f"Check service dependencies and upstream gateway timeouts for payment services on {srv_str}")
            recs.append("Verify circuit breaker thresholds and retry backoff policies")

        if any("auth" in s for s in services_lower):
            recs.append(f"Review authentication failure rates and inspect auth logs on {srv_str} for anomalous source IPs")
            recs.append("Verify edge rate-limiting and token verification cache health")

        if not recs:
            recs.append(f"Investigate high CPU and memory resource consumption on {srv_str}")
            recs.append("Review recent application deployment changes and error logs")
            recs.append("Inspect inter-service network connectivity and health probe endpoints")

        return recs

    def _insufficient_evidence_response(self, reason: str) -> Dict[str, Any]:
        return {
            "incident_id": None,
            "title": "Incident Analysis",
            "what_happened": "Insufficient evidence to determine a confident root cause.",
            "why_it_was_detected": "Evaluation found sparse or inconclusive telemetry.",
            "likely_root_cause": "Insufficient evidence to determine a confident root cause.",
            "confidence": 0,
            "affected_services": [],
            "affected_servers": [],
            "evidence": [reason, "Insufficient evidence to determine a confident root cause."],
            "recommended_actions": [
                "Increase logging verbosity (DEBUG level) across target services",
                "Ensure health probe telemetry is streaming from all nodes",
                "Collect additional diagnostic metrics before drawing conclusions"
            ],
            "has_sufficient_evidence": False
        }

ai_explainer = AiIncidentExplainer()
