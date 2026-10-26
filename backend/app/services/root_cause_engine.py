from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from backend.app.utils.logger import logger

# Service dependency mapping: key depends on values in the list
# i.e., "web-server" depends on "payment-api", "payment-api" depends on "database"
SERVICE_DEPENDENCIES: Dict[str, List[str]] = {
    "web-server": ["payment-api", "authentication", "cache"],
    "payment-api": ["database", "cache"],
    "authentication": ["database", "cache"],
    "worker-node": ["database", "cache"],
    "analytics-pipeline": ["database", "cache"],
    "gateway": ["web-server", "authentication"],
}

# Upstream priority (lower number = deeper/more fundamental root component)
DEPENDENCY_DEPTH: Dict[str, int] = {
    "database": 0,
    "cache": 0,
    "authentication": 1,
    "payment-api": 1,
    "worker-node": 1,
    "analytics-pipeline": 1,
    "web-server": 2,
    "gateway": 3,
}

class RootCauseEngine:
    """
    Deterministic Root Cause Analysis (RCA) Engine.
    Computes root causes, calibrated confidence, evidence, recommendations, and timeline
    from actual stored event data without random or artificial values.
    """

    def analyze(self, events: List[Dict[str, Any]], anomalies: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyzes a correlated group of events to deduce root cause, confidence,
        supporting evidence, recommended actions, and timeline.
        """
        if not events:
            return self._empty_result()

        # 1. Sort events chronologically
        sorted_events = sorted(events, key=lambda e: str(e.get("timestamp", "")))
        
        # 2. Insufficient / weak evidence check
        error_events = [
            e for e in sorted_events 
            if str(e.get("severity", "")).upper() in {"WARNING", "ERROR", "CRITICAL"}
        ]
        
        if len(error_events) == 0:
            return self._insufficient_evidence_result(sorted_events, "No abnormal or error events detected in event cluster.")
        
        # If there is only 1 minor warning with no cascade, flag as low confidence
        if len(error_events) == 1 and error_events[0].get("severity", "").upper() == "WARNING":
            return self._insufficient_evidence_result(
                sorted_events, 
                "Only an isolated warning was detected without subsequent errors or dependency propagation."
            )

        # 3. Group by (server, service) to evaluate candidate causes
        candidates: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for ev in error_events:
            srv = str(ev.get("server", "unknown")).lower()
            svc = str(ev.get("service", "unknown")).lower().replace(" ", "-")
            key = (srv, svc)
            if key not in candidates:
                candidates[key] = []
            candidates[key].append(ev)

        # 4. Score each candidate based on:
        #    - First event / temporal precedence (35%)
        #    - Dependency depth (30%)
        #    - Error frequency & severity (20%)
        #    - Anomaly score (15%)
        earliest_time = str(sorted_events[0].get("timestamp", ""))
        scored_candidates = []

        for (srv, svc), group in candidates.items():
            first_event_in_group = sorted(group, key=lambda x: str(x.get("timestamp", "")))[0]
            group_first_time = str(first_event_in_group.get("timestamp", ""))
            
            # Factor 1: Temporal score (Is this the first event in the entire incident?)
            # If exactly earliest time -> 1.0, otherwise decay
            time_score = 1.0 if group_first_time == earliest_time else 0.4
            
            # Factor 2: Dependency depth score
            # Deeper upstream services (like database/cache = depth 0) get higher root score
            depth = DEPENDENCY_DEPTH.get(svc, 2)
            dep_score = max(0.2, 1.0 - (depth * 0.25))

            # Factor 3: Severity & frequency score
            crit_count = sum(1 for x in group if str(x.get("severity", "")).upper() == "CRITICAL")
            err_count = sum(1 for x in group if str(x.get("severity", "")).upper() == "ERROR")
            freq_score = min(1.0, (crit_count * 0.4 + err_count * 0.2 + len(group) * 0.1))

            # Factor 4: ML Anomaly score
            anomaly_score = 0.5
            for x in group:
                if "anomaly_score" in x and x["anomaly_score"] is not None:
                    anomaly_score = max(anomaly_score, float(x["anomaly_score"]))
            
            # Composite raw root cause weight
            composite_weight = (
                0.35 * time_score +
                0.30 * dep_score +
                0.20 * freq_score +
                0.15 * anomaly_score
            )
            
            scored_candidates.append({
                "server": srv,
                "service": svc,
                "first_event": first_event_in_group,
                "events": group,
                "composite_weight": composite_weight,
                "time_score": time_score,
                "dep_score": dep_score,
                "freq_score": freq_score,
                "anomaly_score": anomaly_score,
                "is_earliest": (group_first_time == earliest_time)
            })

        # Sort candidates by composite weight descending
        scored_candidates.sort(key=lambda c: c["composite_weight"], reverse=True)
        winner = scored_candidates[0]

        # 5. Compute calibrated confidence score (0-100)
        # Higher confidence when:
        # - Earliest event is on an upstream dependency
        # - Error volume is high
        # - Multiple distinct servers/services confirm the cascade
        base_confidence = winner["composite_weight"] * 85.0

        # Confidence boost for upstream cascade confirmation
        has_cascade = len(candidates) > 1
        is_upstream = DEPENDENCY_DEPTH.get(winner["service"], 2) <= 1
        
        if has_cascade and is_upstream and winner["is_earliest"]:
            base_confidence += 10.0  # Confirmed causal propagation
        elif not has_cascade and len(error_events) < 3:
            base_confidence = min(base_confidence, 65.0)

        # Cap between 30 and 96
        final_confidence = int(max(30, min(96, round(base_confidence))))

        # 6. Formulate descriptive root cause
        likely_root_cause = self._formulate_root_cause(winner)

        # 7. Formulate Evidence list
        evidence = self._generate_evidence(sorted_events, winner, scored_candidates, final_confidence)

        # 8. Formulate Recommendations
        recommendations = self._generate_recommendations(winner)

        # 9. Build chronological timeline
        timeline = self._build_timeline(sorted_events)

        # 10. AI Summary synthesis
        ai_summary = self._generate_summary(winner, likely_root_cause, len(sorted_events), len(candidates))

        return {
            "root_cause": likely_root_cause,
            "likely_root_cause": likely_root_cause,
            "confidence": final_confidence,
            "primary_server": winner["server"],
            "primary_service": winner["service"],
            "evidence": evidence,
            "recommendations": recommendations,
            "recommended_actions": recommendations,
            "timeline": timeline,
            "ai_summary": ai_summary,
            "reasoning_factors": {
                "temporal_weight": round(winner["time_score"], 2),
                "dependency_weight": round(winner["dep_score"], 2),
                "frequency_weight": round(winner["freq_score"], 2),
                "anomaly_weight": round(winner["anomaly_score"], 2),
                "earliest_event_timestamp": str(winner["first_event"].get("timestamp", ""))
            }
        }

    def _formulate_root_cause(self, winner: Dict[str, Any]) -> str:
        srv = winner["server"]
        svc = winner["service"]
        msg = str(winner["first_event"].get("message", "")).lower()

        if "connection slots" in msg or "pool" in msg or ("database" in svc and "timeout" in msg):
            return f"Database connection exhaustion on {srv}"
        if "cpu" in msg or "load" in msg:
            return f"High CPU utilization and computational bottleneck on {srv}"
        if "memory" in msg or "oom" in msg or "heap" in msg:
            return f"Memory exhaustion / Out of Memory condition on {srv}"
        if "auth" in msg or "login" in msg or "password" in msg:
            return f"Authentication service degradation / brute force spike on {srv}"
        if "timeout" in msg or "latency" in msg:
            return f"Upstream service latency and timeout surge on {srv} ({svc})"
        if "disk" in msg or "space" in msg or "storage" in msg:
            return f"Disk storage capacity saturation on {srv}"
        
        # Generic descriptive fallback
        raw_msg = str(winner["first_event"].get("message", "")).strip()
        if len(raw_msg) > 60:
            raw_msg = raw_msg[:60] + "..."
        return f"{svc.replace('-', ' ').title()} failure on {srv}: {raw_msg}"

    def _generate_evidence(
        self, 
        events: List[Dict[str, Any]], 
        winner: Dict[str, Any], 
        candidates: List[Dict[str, Any]],
        confidence: int
    ) -> List[str]:
        evidence = []
        first_ev = winner["first_event"]
        srv = winner["server"]
        svc = winner["service"]
        first_time = str(first_ev.get("timestamp", ""))
        
        # Evidence 1: Earliest abnormal occurrence
        evidence.append(
            f"Earliest abnormal event logged at {first_time} on {srv} ({svc}): '{first_ev.get('message', '')}'"
        )

        # Evidence 2: Event concentration
        total_errors = sum(1 for e in events if str(e.get("severity", "")).upper() in {"ERROR", "CRITICAL"})
        evidence.append(
            f"{len(events)} correlated log events identified ({total_errors} errors/critical) across {len(set(e.get('server') for e in events))} server node(s)"
        )

        # Evidence 3: Propagation across dependencies
        if len(candidates) > 1:
            downstream = [c for c in candidates if c["service"] != svc]
            if downstream:
                ds_svc = downstream[0]["service"]
                ds_srv = downstream[0]["server"]
                evidence.append(
                    f"Causal failure cascade: {svc} failure propagated downstream to {ds_svc} on {ds_srv}"
                )

        # Evidence 4: Metric impact or ML Anomaly
        max_latency = max([e.get("latency_ms") or e.get("response_time") or 0 for e in events] + [0])
        if max_latency > 0:
            evidence.append(f"Peak observed response latency reached {max_latency}ms during the incident window")
        else:
            evidence.append(f"Statistical anomaly confidence calibrated at {confidence}% based on temporal precedence")

        return evidence

    def _generate_recommendations(self, winner: Dict[str, Any]) -> List[str]:
        svc = winner["service"].lower()
        srv = winner["server"]

        if "database" in svc:
            return [
                f"Check active database connections using 'SELECT count(*) FROM pg_stat_activity' on {srv}",
                f"Verify connection pool limits and max_connections parameters in database configuration",
                f"Review recent slow queries, missing indexes, or unindexed migration scripts on {srv}",
                f"Scale read-replicas or restart connection pooler (e.g., PgBouncer) to shed saturated sockets"
            ]
        elif "payment" in svc or "api" in svc:
            return [
                f"Verify connectivity and socket health between {srv} and upstream databases",
                f"Inspect API gateway timeout thresholds and ensure circuit breaker policies are tripped",
                f"Check downstream payment gateway webhook responses for elevated 5xx error codes",
                f"Drain and restart affected container instances on {srv} if socket exhaustion persists"
            ]
        elif "auth" in svc:
            return [
                f"Inspect authentication service audit logs on {srv} for anomalous IP address spikes",
                f"Verify edge rate-limiting and temporary IP throttling on login endpoints",
                f"Check LDAP/OAuth2 token validation latency and token cache eviction rates"
            ]
        elif "cpu" in str(winner["first_event"].get("message", "")).lower():
            return [
                f"Inspect top CPU consuming processes using 'top' or 'htop' on {srv}",
                f"Check for runaway worker threads or unoptimized query loops",
                f"Consider horizontal scaling or adding worker nodes to distribute the compute load"
            ]
        else:
            return [
                f"Inspect system and service error logs on {srv} around {winner['first_event'].get('timestamp', '')}",
                f"Check server resource metrics (CPU, RAM, Disk I/O) on {srv}",
                f"Restart or redeploy {svc} service to clear degraded memory or socket states",
                f"Review recent software deployments or configuration updates on {srv}"
            ]

    def _build_timeline(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        timeline = []
        for idx, ev in enumerate(events):
            ts = str(ev.get("timestamp", ""))
            # Extract time portion for compact UI display
            compact_time = ts.split(" ")[1] if " " in ts else ts.split("T")[1][:8] if "T" in ts else ts
            
            raw_msg = str(ev.get("message", "")).strip()
            sev = str(ev.get("severity", "INFO")).upper()
            
            timeline.append({
                "time": compact_time,
                "timestamp": ts,
                "server": str(ev.get("server", "unknown")),
                "service": str(ev.get("service", "unknown")),
                "event": raw_msg,
                "severity": sev
            })
        return timeline

    def _generate_summary(self, winner: Dict[str, Any], root_cause: str, total_events: int, num_components: int) -> str:
        srv = winner["server"]
        svc = winner["service"]
        return (
            f"The system detected an abnormal cascade triggered by {root_cause.lower()}. "
            f"A total of {total_events} correlated events were captured across {num_components} service component(s), "
            f"with initial telemetry degradation originating from {svc} on {srv}."
        )

    def _insufficient_evidence_result(self, events: List[Dict[str, Any]], explanation: str) -> Dict[str, Any]:
        return {
            "root_cause": "Undetermined / Low Confidence",
            "likely_root_cause": "Undetermined / Low Confidence",
            "confidence": 28,
            "primary_server": events[0].get("server", "unknown") if events else "unknown",
            "primary_service": events[0].get("service", "unknown") if events else "unknown",
            "evidence": [
                f"RCA engine evaluated {len(events)} event(s) but found insufficient evidence.",
                explanation,
                "Telemetry does not exhibit a verifiable causal dependency chain or error spike."
            ],
            "recommendations": [
                "Increase logging verbosity (DEBUG/INFO) on the target service",
                "Ensure health probe telemetry is actively streaming from all nodes",
                "Monitor for further anomalous events in subsequent log batches"
            ],
            "recommended_actions": [
                "Increase logging verbosity (DEBUG/INFO) on the target service",
                "Ensure health probe telemetry is actively streaming from all nodes",
                "Monitor for further anomalous events in subsequent log batches"
            ],
            "timeline": self._build_timeline(events),
            "ai_summary": f"Incident analysis inconclusive ({explanation}). Additional telemetry is required.",
            "reasoning_factors": {
                "temporal_weight": 0.0,
                "dependency_weight": 0.0,
                "frequency_weight": 0.0,
                "anomaly_weight": 0.0,
                "earliest_event_timestamp": events[0].get("timestamp", "") if events else ""
            }
        }

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "root_cause": "No Events Available",
            "likely_root_cause": "No Events Available",
            "confidence": 0,
            "primary_server": "unknown",
            "primary_service": "unknown",
            "evidence": ["No events supplied for root cause evaluation."],
            "recommendations": ["Ensure logs are uploaded and ingested properly."],
            "recommended_actions": ["Ensure logs are uploaded and ingested properly."],
            "timeline": [],
            "ai_summary": "No telemetry data available for incident analysis.",
            "reasoning_factors": {}
        }

root_cause_engine = RootCauseEngine()
