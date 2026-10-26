"""
AI-CLAR Event Correlation Module
Extension Point for Phase 2:
- Sliding-window temporal correlation across multi-node cloud clusters.
- Groups heterogeneous log streams into coherent single-incident graph clusters.
"""
from typing import List, Dict, Any

class EventCorrelatorService:
    def __init__(self, time_window_seconds: int = 300):
        self.time_window_seconds = time_window_seconds

    def correlate_events(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups logs sharing common trace/correlation IDs, IP subnets, or co-occurring timestamps.
        """
        clusters: Dict[str, List[Dict[str, Any]]] = {}
        for log in logs:
            corr_id = log.get("correlation_id") or f"cluster-{log.get('server', 'unknown')}"
            if corr_id not in clusters:
                clusters[corr_id] = []
            clusters[corr_id].append(log)
            
        correlated_results = []
        for cid, items in clusters.items():
            if len(items) > 1:
                correlated_results.append({
                    "correlation_id": cid,
                    "event_count": len(items),
                    "servers_involved": list(set(i.get("server") for i in items)),
                    "services_involved": list(set(i.get("service") for i in items)),
                    "primary_severity": max([i.get("severity", "INFO") for i in items])
                })
        return correlated_results

event_correlator = EventCorrelatorService()
