import re
import uuid
from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import datetime, timezone

from backend.app.database.connection import db
from backend.app.models.incident import IncidentModel, IncidentStatus, IncidentSeverity
from backend.app.services.root_cause_engine import root_cause_engine, SERVICE_DEPENDENCIES
from backend.app.services.alert_service import alert_service
from backend.app.utils.logger import logger

def _parse_ts(ts_str: str) -> float:
    """Safely parses timestamp string into Unix epoch seconds."""
    if not ts_str:
        return 0.0
    ts_clean = str(ts_str).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(ts_clean[:19], fmt[:19]).timestamp()
        except ValueError:
            continue
    return 0.0

class EventCorrelator:
    """
    Multi-Factor Cloud Event Correlator.
    Correlates related log events using:
    - Temporal proximity (sliding time window)
    - Server locality
    - Service dependency topology (upstream -> downstream cascade)
    - Severity & error categorization
    - Error message signatures
    - ML anomaly scores
    
    Ensures unrelated errors remain strictly separate and normal logs do not trigger incidents.
    """

    def __init__(self, time_window_seconds: int = 600):
        self.time_window_seconds = time_window_seconds

    def is_candidate_event(self, log: Dict[str, Any]) -> bool:
        """
        Determines if a log entry qualifies as an incident candidate.
        Normal INFO traffic is strictly filtered out.
        """
        sev = str(log.get("severity", "")).upper()
        if sev in {"ERROR", "CRITICAL"}:
            return True
        if sev == "WARNING":
            # Significant warnings participate in correlation
            msg = str(log.get("message", "")).lower()
            cpu = float(log.get("cpu_usage") or 0)
            mem = float(log.get("memory_usage") or 0)
            status_code = int(log.get("status_code") or 0)
            if cpu >= 75.0 or mem >= 80.0 or status_code >= 400:
                return True
            if any(k in msg for k in ["high cpu", "near capacity", "high latency", "slow", "timeout", "exhaustion", "saturation"]):
                return True
            return False
            
        status_code = int(log.get("status_code") or 0)
        if status_code >= 500:
            return True

        if log.get("anomaly_score") and float(log["anomaly_score"]) >= 0.70:
            return True

        return False

    def are_events_related(self, e1: Dict[str, Any], e2: Dict[str, Any]) -> bool:
        """
        Determines if two abnormal events belong to the same incident cluster.
        """
        # 1. Temporal Proximity Check
        t1 = _parse_ts(e1.get("timestamp", ""))
        t2 = _parse_ts(e2.get("timestamp", ""))
        if t1 > 0 and t2 > 0:
            time_diff = abs(t1 - t2)
            if time_diff > self.time_window_seconds:
                return False
        
        # 2. Same Correlation ID
        c1 = str(e1.get("correlation_id") or "").strip()
        c2 = str(e2.get("correlation_id") or "").strip()
        if c1 and c2 and c1 == c2:
            return True

        srv1 = str(e1.get("server", "s1")).lower()
        srv2 = str(e2.get("server", "s2")).lower()
        svc1 = str(e1.get("service", "")).lower().replace(" ", "-")
        svc2 = str(e2.get("service", "")).lower().replace(" ", "-")

        # 3. Same Server Check (e.g. CPU warning + app crash on same server)
        if srv1 == srv2:
            return True

        # 4. Service Dependency Check (across different servers)
        # e.g., web-server depends on payment-api, payment-api depends on database
        deps1 = SERVICE_DEPENDENCIES.get(svc1, [])
        deps2 = SERVICE_DEPENDENCIES.get(svc2, [])
        msg1 = str(e1.get("message", "")).lower()
        msg2 = str(e2.get("message", "")).lower()
        status1 = int(e1.get("status_code") or 0)
        status2 = int(e2.get("status_code") or 0)

        cascade_keywords = [
            "timeout", "timed out", "pool", "connection refused", "connection error", 
            "gateway", "upstream", "database", "postgres", "redis", "latency"
        ]

        # If svc1 depends on svc2 (svc1 is downstream, svc2 is upstream)
        if svc2 in deps1:
            has_symptom = (
                status1 in {500, 502, 503, 504} or
                svc2 in msg1 or
                any(kw in msg1 for kw in cascade_keywords)
            )
            if has_symptom:
                return True

        # If svc2 depends on svc1 (svc2 is downstream, svc1 is upstream)
        if svc1 in deps2:
            has_symptom = (
                status2 in {500, 502, 503, 504} or
                svc1 in msg2 or
                any(kw in msg2 for kw in cascade_keywords)
            )
            if has_symptom:
                return True

        # 5. Shared Error Pattern / Target Keyword
        msg1 = str(e1.get("message", "")).lower()
        msg2 = str(e2.get("message", "")).lower()
        shared_keywords = ["database", "postgres", "redis", "timeout", "connection pool", "gateway timeout"]
        for kw in shared_keywords:
            if kw in msg1 and kw in msg2:
                # If both mention the same infrastructure failure within time window
                return True

        # Otherwise, distinct servers with unrelated services remain separate
        return False

    def cluster_events(self, events: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Partitions candidate events into connected components (clusters).
        """
        candidates = [e for e in events if self.is_candidate_event(e)]
        if not candidates:
            return []

        # Sort chronologically
        candidates.sort(key=lambda e: str(e.get("timestamp", "")))
        n = len(candidates)
        visited = [False] * n
        clusters: List[List[Dict[str, Any]]] = []

        for i in range(n):
            if visited[i]:
                continue
            
            # Start a new cluster using BFS
            cluster = [candidates[i]]
            visited[i] = True
            queue = [i]

            while queue:
                curr = queue.pop(0)
                for j in range(n):
                    if not visited[j]:
                        if self.are_events_related(candidates[curr], candidates[j]):
                            visited[j] = True
                            cluster.append(candidates[j])
                            queue.append(j)

            clusters.append(cluster)

        return clusters

    def formulate_incident_title(self, cluster: List[Dict[str, Any]], primary_service: str, primary_server: str) -> str:
        """Formulates an informative, professional incident title."""
        services = sorted(list(set(str(e.get("service", "")).lower().replace(" ", "-") for e in cluster)))
        messages = " ".join(str(e.get("message", "")).lower() for e in cluster)

        if "database" in services and "payment-api" in services:
            return "Database Connectivity Failure & Payment API Timeout"
        if "connection slots" in messages or ("database" in services and "timeout" in messages):
            return f"Database Connection Exhaustion ({primary_server})"
        if "cpu" in messages or "load" in messages:
            return f"High CPU Utilization & Service Degradation ({primary_server})"
        if "auth" in services or "login" in messages:
            return f"Authentication Service Degradation ({primary_server})"
        if "payment" in services or "checkout" in messages:
            return f"Payment API Gateway Degradation ({primary_server})"
        if "504" in messages or "gateway timeout" in messages:
            return f"Gateway Timeout Surge ({primary_server})"
        
        svc_name = primary_service.replace("-", " ").title()
        return f"{svc_name} Service Outage on {primary_server}"

    def correlate_and_create_incidents(self, new_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main pipeline hook:
        1. Clusters candidate logs
        2. Performs RCA on each cluster
        3. Updates active incidents or inserts new incidents into MongoDB / in-memory DB
        """
        clusters = self.cluster_events(new_logs)
        created_or_updated: List[Dict[str, Any]] = []

        for idx, cluster in enumerate(clusters):
            # Run RCA engine on this cluster
            rca_result = root_cause_engine.analyze(cluster)
            
            # Time bounds
            sorted_cluster = sorted(cluster, key=lambda e: str(e.get("timestamp", "")))
            start_time = str(sorted_cluster[0].get("timestamp", ""))
            end_time = str(sorted_cluster[-1].get("timestamp", ""))
            
            affected_servers = sorted(list(set(str(e.get("server", "unknown")) for e in cluster)))
            affected_services = sorted(list(set(str(e.get("service", "unknown")) for e in cluster)))
            related_ids = [str(e.get("id") or e.get("_id") or f"log-{i}") for i, e in enumerate(cluster)]

            # Determine severity
            has_critical = any(str(e.get("severity", "")).upper() == "CRITICAL" for e in cluster)
            has_error = any(str(e.get("severity", "")).upper() == "ERROR" for e in cluster)
            if has_critical:
                sev = IncidentSeverity.CRITICAL
            elif has_error or len(cluster) >= 3:
                sev = IncidentSeverity.HIGH
            else:
                sev = IncidentSeverity.MEDIUM

            # Title
            title = self.formulate_incident_title(cluster, rca_result["primary_service"], rca_result["primary_server"])

            # Check if there is an active incident on the same primary server/service within recent window
            active_existing = db.incidents.find_one({
                "status": {"$in": [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING, "Open", "Investigating"]},
                "affected_server": {"$in": affected_servers}
            })

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            if active_existing:
                # Merge into existing incident
                inc_id = active_existing.get("incident_id") or active_existing.get("id")
                existing_related = set(active_existing.get("related_event_ids", []))
                existing_related.update(related_ids)
                
                all_servers = sorted(list(set(active_existing.get("affected_servers", []) + affected_servers)))
                all_services = sorted(list(set(active_existing.get("affected_services", []) + affected_services)))
                
                update_fields = {
                    "end_time": end_time,
                    "affected_servers": all_servers,
                    "affected_services": all_services,
                    "related_event_ids": list(existing_related),
                    "related_events_count": len(existing_related),
                    "root_cause": rca_result["root_cause"],
                    "likely_root_cause": rca_result["likely_root_cause"],
                    "confidence": rca_result["confidence"],
                    "evidence": rca_result["evidence"],
                    "recommendations": rca_result["recommendations"],
                    "recommended_actions": rca_result["recommendations"],
                    "timeline": rca_result["timeline"],
                    "ai_summary": rca_result["ai_summary"],
                    "updated_at": now_str
                }
                
                db.incidents.update_one({"id": inc_id}, {"$set": update_fields})
                merged_doc = {**active_existing, **update_fields}
                created_or_updated.append(merged_doc)
                logger.info("Updated active incident '%s' with %d new events.", inc_id, len(cluster))
                if str(merged_doc.get("severity", "")).upper() == "CRITICAL":
                    alert_service.create_alert_for_incident(merged_doc)
            else:
                # Create brand new incident
                inc_id = f"inc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}-{idx+1:02d}"
                incident_obj = IncidentModel(
                    incident_id=inc_id,
                    title=title,
                    severity=sev,
                    status=IncidentStatus.INVESTIGATING if sev == IncidentSeverity.CRITICAL else IncidentStatus.OPEN,
                    start_time=start_time,
                    end_time=end_time,
                    affected_servers=affected_servers,
                    affected_services=affected_services,
                    related_event_ids=related_ids,
                    root_cause=rca_result["root_cause"],
                    confidence=rca_result["confidence"],
                    evidence=rca_result["evidence"],
                    recommendations=rca_result["recommendations"],
                    created_at=now_str,
                    updated_at=now_str,
                    ai_summary=rca_result["ai_summary"],
                    timeline=rca_result["timeline"]
                )
                
                doc = incident_obj.to_dict()
                db.incidents.insert_one(doc)
                created_or_updated.append(doc)
                logger.info("Generated new incident '%s': '%s' (Severity: %s, Confidence: %d%%)", inc_id, title, sev, rca_result["confidence"])
                if sev == IncidentSeverity.CRITICAL or str(doc.get("severity", "")).upper() == "CRITICAL":
                    alert_service.create_alert_for_incident(doc)

        return created_or_updated

event_correlator = EventCorrelator()
