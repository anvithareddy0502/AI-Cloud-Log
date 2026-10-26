from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import math

class FeatureExtractor:
    """
    Extracts numerical and categorical telemetry features per server over sliding time windows.
    """

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes

    def extract_features(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups logs by server and time window, calculating statistical feature vectors.
        """
        if not logs:
            return []

        # 1. Bucket logs by (server, time_window_start)
        buckets: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

        for log in logs:
            server = log.get("server", "server-01").lower()
            ts_str = log.get("timestamp")
            window_key = self._get_window_key(ts_str)
            key = (server, window_key)
            if key not in buckets:
                buckets[key] = []
            buckets[key].append(log)

        # 2. Compute metrics for each bucket
        feature_records = []
        for (server, window_str), bucket_logs in buckets.items():
            features = self._calculate_bucket_features(server, window_str, bucket_logs)
            feature_records.append(features)

        # Sort chronologically
        feature_records.sort(key=lambda x: (x["server"], x["time_window"]))
        return feature_records

    def _get_window_key(self, ts_str: Optional[str]) -> str:
        try:
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            dt = datetime.now()

        # Floor to window_minutes boundary
        minute_floor = (dt.minute // self.window_minutes) * self.window_minutes
        window_start = dt.replace(minute=minute_floor, second=0, microsecond=0)
        window_end = window_start + timedelta(minutes=self.window_minutes)
        return f"{window_start.strftime('%Y-%m-%d %H:%M')} - {window_end.strftime('%H:%M')}"

    def _calculate_bucket_features(self, server: str, window_str: str, bucket_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_events = len(bucket_logs)
        error_count = 0
        warning_count = 0
        info_count = 0
        critical_count = 0
        http_4xx_count = 0
        http_5xx_count = 0
        failed_login_count = 0
        response_times: List[float] = []
        services_involved = set()

        unique_event_ids = set()
        for l in bucket_logs:
            sev = str(l.get("severity", "INFO")).upper()
            if sev == "CRITICAL":
                critical_count += 1
            elif sev == "ERROR":
                error_count += 1
            elif sev == "WARNING":
                warning_count += 1
            else:
                info_count += 1

            svc = l.get("service", "unknown")
            services_involved.add(svc)

            eid = l.get("event_id") or l.get("event_template")
            if eid:
                unique_event_ids.add(str(eid))

            # HTTP Status Code checks
            sc = l.get("status_code")
            if sc:
                if 400 <= sc < 500:
                    http_4xx_count += 1
                elif 500 <= sc < 600:
                    http_5xx_count += 1

            # Response time
            rt = l.get("response_time")
            if rt is None:
                rt = l.get("response_time_ms")
            if rt is not None and not math.isnan(float(rt)):
                response_times.append(float(rt))

            # Failed Login detection
            msg = str(l.get("message", "")).lower()
            if "auth" in svc.lower() or "login" in msg or "auth" in msg:
                if sc in {401, 403} or "fail" in msg or sev in {"WARNING", "ERROR", "CRITICAL"}:
                    failed_login_count += 1

        error_rate = round((error_count + critical_count) / total_events, 4) if total_events > 0 else 0.0
        warning_rate = round(warning_count / total_events, 4) if total_events > 0 else 0.0
        events_per_minute = round(total_events / max(self.window_minutes, 1), 2)
        avg_rt = round(sum(response_times) / len(response_times), 2) if response_times else 25.0
        max_rt = round(max(response_times), 2) if response_times else 25.0

        # Template Shannon Entropy
        template_entropy = 0.0
        if unique_event_ids and total_events > 0:
            counts = {}
            for l in bucket_logs:
                key = str(l.get("event_id") or l.get("event_template") or "default")
                counts[key] = counts.get(key, 0) + 1
            template_entropy = round(
                -sum((c / total_events) * math.log2(c / total_events) for c in counts.values()), 4
            )

        # Check if ground-truth labels exist
        labeled_flags = [l.get("is_anomaly_label") for l in bucket_logs if l.get("is_anomaly_label") is not None]
        is_anomaly_label = 1 if (labeled_flags and any(f == 1 for f in labeled_flags)) else (0 if labeled_flags else None)

        return {
            "server": server,
            "services": list(services_involved),
            "time_window": window_str,
            # Core Features
            "total_events": total_events,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "critical_count": critical_count,
            "error_rate": error_rate,
            "warning_rate": warning_rate,
            "events_per_minute": events_per_minute,
            "events_per_time_window": total_events,
            "unique_event_ids": len(unique_event_ids),
            "unique_components": len(services_involved),
            "template_entropy": template_entropy,
            "avg_response_time": avg_rt,
            "max_response_time": max_rt,
            "http_4xx_count": http_4xx_count,
            "http_5xx_count": http_5xx_count,
            "failed_login_count": failed_login_count,
            # Ground-truth tag (None for unlabeled datasets)
            "is_anomaly_label": is_anomaly_label,
            # Backward-compatibility aliases
            "average_response_time": avg_rt,
            "maximum_response_time": max_rt,
            "HTTP_4xx_count": http_4xx_count,
            "HTTP_5xx_count": http_5xx_count
        }

    def extract_dataset_features(
        self,
        logs: List[Dict[str, Any]],
        window_size: int = 20,
        step_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Extracts sliding event-count window feature vectors across sequential log datasets.
        Generates approximately (N - window_size) // step_size + 1 samples.
        """
        if not logs or len(logs) < window_size:
            return []

        feature_records = []
        for start in range(0, len(logs) - window_size + 1, step_size):
            window_logs = logs[start : start + window_size]
            server = window_logs[0].get("server", "cluster-node")
            t_start = window_logs[0].get("timestamp", f"w-{start}")
            t_end = window_logs[-1].get("timestamp", f"w-{start+window_size}")
            window_str = f"{t_start} - {t_end}"

            feat = self._calculate_bucket_features(server, window_str, window_logs)
            feat["window_index"] = len(feature_records)
            feature_records.append(feat)

        return feature_records

feature_extractor = FeatureExtractor()

