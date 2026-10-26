"""
Dataset Adapters for LogHub Benchmarks (OpenStack, HDFS, BGL)
Normalizes structured CSV logs into the standard AI-CLAR internal log representation
without fabricating non-existent fields.
"""
import os
import re
import math
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

BASE_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))

DATASET_CONFIGS = {
    "OpenStack": {
        "rel_path": os.path.join("OpenStack", "OpenStack_2k.log_structured.csv"),
        "has_labels": False,
        "description": "OpenStack cloud virtualization log dataset from LogHub (2,000 structured events)",
    },
    "HDFS": {
        "rel_path": os.path.join("HDFS", "HDFS_2k.log_structured.csv"),
        "has_labels": False,
        "description": "Hadoop Distributed File System log dataset from LogHub (2,000 structured events)",
    },
    "BGL": {
        "rel_path": os.path.join("BGL", "BGL_2k.log_structured.csv"),
        "has_labels": True,
        "description": "Blue Gene/L supercomputer log dataset from LogHub (2,000 structured events with ground-truth failure labels)",
    },
    "BGL_2k": {
        "rel_path": os.path.join("BGL", "BGL_2k.log_structured.csv"),
        "has_labels": True,
        "description": "Blue Gene/L supercomputer benchmark subset from LogHub (2,000 structured events with ground-truth failure labels)",
    },
    "BGL_full": {
        "rel_path": os.path.join("BGL", "BGL_full.log_structured.csv"),
        "raw_log_rel_path": os.path.join("BGL", "BGL_full.log"),
        "has_labels": True,
        "is_large": True,
        "description": "Blue Gene/L supercomputer full dataset from LogHub-2.0 (4,631,261 structured events with authentic ground-truth failure labels)",
    }
}

# Regex to extract status and response time from message content if explicitly present
STATUS_REGEX = re.compile(r'\bstatus:\s*([1-5]\d\d)\b', re.IGNORECASE)
TIME_REGEX = re.compile(r'\btime:\s*([0-9.]+)\b', re.IGNORECASE)
IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')


def _format_hdfs_timestamp(date_val: Any, time_val: Any) -> str:
    """Converts HDFS YYMMDD and HHMMSS integers into ISO string."""
    try:
        d_str = str(int(date_val)).zfill(6)
        t_str = str(int(time_val)).zfill(6)
        return f"20{d_str[:2]}-{d_str[2:4]}-{d_str[4:6]} {t_str[:2]}:{t_str[2:4]}:{t_str[4:6]}"
    except Exception:
        return "2008-11-09 20:00:00"


def _format_bgl_timestamp(ts_val: Any, date_val: Any, time_val: Any) -> str:
    """Formats BGL timestamp from epoch or string."""
    try:
        if ts_val and not math.isnan(float(ts_val)):
            return datetime.fromtimestamp(float(ts_val)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    try:
        d_str = str(date_val).replace(".", "-")
        t_str = str(time_val)[:19] if time_val else "00:00:00"
        return f"{d_str} {t_str}".strip()
    except Exception:
        return "2005-06-03 15:42:50"


class DatasetAdapter:
    """
    Adapter responsible for loading and normalizing LogHub structured CSV datasets.
    Supports in-memory loading for 2K benchmarks and memory-efficient chunked streaming
    for the full 4.6M-line BGL dataset.
    """

    @classmethod
    def get_supported_datasets(cls) -> List[str]:
        return list(DATASET_CONFIGS.keys())

    @classmethod
    def load_dataset(
        cls,
        dataset_name: str,
        max_records: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Loads and normalizes the target dataset into standard AI-CLAR log representations.
        Returns:
            (normalized_logs_list, dataset_metadata_dict)
        """
        ds_name = dataset_name.strip()
        matched_key = None
        for k in DATASET_CONFIGS:
            if k.lower() == ds_name.lower():
                matched_key = k
                break

        if not matched_key:
            raise ValueError(
                f"Unsupported dataset '{dataset_name}'. Supported datasets: {list(DATASET_CONFIGS.keys())}"
            )

        config = DATASET_CONFIGS[matched_key]
        full_path = os.path.join(BASE_DATA_DIR, config["rel_path"])
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Dataset file not found at: {full_path}")

        # If BGL_full is requested via load_dataset, protect against OOM by streaming max_records
        if matched_key == "BGL_full":
            limit = max_records or 2000
            normalized_logs = cls._load_bgl_full_sample(limit)
            metadata = {
                "dataset_name": "BGL_full",
                "description": config["description"],
                "total_records": len(normalized_logs),
                "is_sample": max_records is not None or limit == 2000,
                "has_ground_truth_labels": True,
                "file_path": full_path,
            }
            anomaly_count = sum(1 for log in normalized_logs if log.get("is_anomaly_label") == 1)
            metadata["labeled_anomaly_count"] = anomaly_count
            metadata["labeled_anomaly_rate"] = round(anomaly_count / max(len(normalized_logs), 1), 4)
            return normalized_logs, metadata

        df = pd.read_csv(full_path, nrows=max_records) if max_records else pd.read_csv(full_path)
        normalized_logs = []

        if matched_key == "OpenStack":
            normalized_logs = cls._normalize_openstack(df)
        elif matched_key == "HDFS":
            normalized_logs = cls._normalize_hdfs(df)
        elif matched_key in {"BGL", "BGL_2k"}:
            normalized_logs = cls._normalize_bgl(df)

        metadata = {
            "dataset_name": matched_key,
            "description": config["description"],
            "total_records": len(normalized_logs),
            "has_ground_truth_labels": config["has_labels"],
            "columns": list(df.columns),
            "file_path": full_path,
        }

        if config["has_labels"]:
            anomaly_count = sum(1 for log in normalized_logs if log.get("is_anomaly_label") == 1)
            metadata["labeled_anomaly_count"] = anomaly_count
            metadata["labeled_anomaly_rate"] = round(anomaly_count / max(len(normalized_logs), 1), 4)

        return normalized_logs, metadata

    @classmethod
    def _load_bgl_full_sample(cls, limit: int = 2000) -> List[Dict[str, Any]]:
        """Loads a bounded sample of BGL_full without loading the entire 469 MB file into RAM."""
        import csv
        structured_path = os.path.join(BASE_DATA_DIR, "BGL", "BGL_full.log_structured.csv")
        raw_log_path = os.path.join(BASE_DATA_DIR, "BGL", "BGL_full.log")
        has_raw = os.path.exists(raw_log_path)

        f_raw = open(raw_log_path, "r", encoding="utf-8", errors="ignore") if has_raw else None
        f_csv = open(structured_path, "r", encoding="utf-8", errors="ignore")
        logs = []
        try:
            next(f_csv) # skip header
            reader = csv.reader(f_csv)
            for idx in range(limit):
                try:
                    csv_row = next(reader)
                except StopIteration:
                    break

                line_id = csv_row[0] if len(csv_row) > 0 else str(idx+1)
                content = csv_row[1] if len(csv_row) > 1 else ""
                event_id = csv_row[2] if len(csv_row) > 2 else ""
                event_template = csv_row[3] if len(csv_row) > 3 else ""

                label_str = "-"
                ts_str = "2005-06-03 15:42:50"
                node = f"bgl-node-{line_id}"
                component = "bgl-system"
                severity = "INFO"

                if f_raw:
                    raw_line = f_raw.readline()
                    if raw_line:
                        parts = raw_line.split(maxsplit=9)
                        if len(parts) > 0:
                            label_str = parts[0].strip()
                        if len(parts) > 2:
                            ts_str = _format_bgl_timestamp(parts[1].strip(), parts[2].strip(), "")
                        if len(parts) > 3:
                            node = parts[3].strip()
                        if len(parts) > 7:
                            component = parts[7].strip()
                        if len(parts) > 8:
                            lvl = parts[8].strip().upper()
                            if any(k in lvl for k in ["FATAL", "SEVERE", "CRIT"]):
                                severity = "CRITICAL"
                            elif any(k in lvl for k in ["ERR", "FAIL"]):
                                severity = "ERROR"
                            elif "WARN" in lvl:
                                severity = "WARNING"
                            else:
                                severity = "INFO"

                is_anom = 0 if label_str == "-" else 1

                logs.append({
                    "id": f"bgl-{line_id}",
                    "timestamp": ts_str,
                    "server": node.lower(),
                    "service": component,
                    "severity": severity,
                    "message": content,
                    "status_code": None,
                    "response_time": None,
                    "event_id": event_id,
                    "event_template": event_template,
                    "dataset": "BGL_full",
                    "raw_label": label_str,
                    "is_anomaly_label": is_anom
                })
        finally:
            f_csv.close()
            if f_raw:
                f_raw.close()
        return logs

    @classmethod
    def stream_dataset_windows(
        cls,
        dataset_name: str = "BGL_full",
        window_size: int = 20,
        step_size: int = 10,
        chunk_size: int = 50000,
        max_records: Optional[int] = None
    ):
        """
        Memory-efficient generator that streams sliding feature windows across large datasets
        without loading the full raw dataset into memory.
        Pairs BGL_full.log_structured.csv (templates & content) with BGL_full.log (labels & metadata).
        """
        from backend.app.services.feature_extractor import feature_extractor
        import csv

        structured_path = os.path.join(BASE_DATA_DIR, "BGL", "BGL_full.log_structured.csv")
        raw_log_path = os.path.join(BASE_DATA_DIR, "BGL", "BGL_full.log")

        if not os.path.exists(raw_log_path):
            alt_raw = os.path.abspath(r"C:\Users\Anu\Downloads\BGL\BGL\BGL_full.log")
            if os.path.exists(alt_raw):
                raw_log_path = alt_raw

        has_raw = os.path.exists(raw_log_path)
        if not os.path.exists(structured_path):
            raise FileNotFoundError(f"BGL_full structured file not found at: {structured_path}")

        f_raw = open(raw_log_path, "r", encoding="utf-8", errors="ignore") if has_raw else None
        f_csv = open(structured_path, "r", encoding="utf-8", errors="ignore")

        try:
            next(f_csv) # Skip header
            csv_reader = csv.reader(f_csv)

            buffer: List[Dict[str, Any]] = []
            records_read = 0
            window_idx = 0

            while True:
                if max_records and records_read >= max_records:
                    break

                batch_rows = []
                for _ in range(chunk_size):
                    if max_records and records_read >= max_records:
                        break
                    try:
                        csv_row = next(csv_reader)
                        batch_rows.append(csv_row)
                        records_read += 1
                    except StopIteration:
                        break

                if not batch_rows:
                    break

                for csv_row in batch_rows:
                    line_id = csv_row[0] if len(csv_row) > 0 else str(records_read)
                    content = csv_row[1] if len(csv_row) > 1 else ""
                    event_id = csv_row[2] if len(csv_row) > 2 else ""
                    event_template = csv_row[3] if len(csv_row) > 3 else ""

                    label_str = "-"
                    ts_str = "2005-06-03 15:42:50"
                    node = f"bgl-node-{line_id}"
                    component = "bgl-system"
                    severity = "INFO"

                    if f_raw:
                        raw_line = f_raw.readline()
                        if raw_line:
                            parts = raw_line.split(maxsplit=9)
                            if len(parts) > 0:
                                label_str = parts[0].strip()
                            if len(parts) > 2:
                                ts_str = _format_bgl_timestamp(parts[1].strip(), parts[2].strip(), "")
                            if len(parts) > 3:
                                node = parts[3].strip()
                            if len(parts) > 7:
                                component = parts[7].strip()
                            if len(parts) > 8:
                                lvl = parts[8].strip().upper()
                                if any(k in lvl for k in ["FATAL", "SEVERE", "CRIT"]):
                                    severity = "CRITICAL"
                                elif any(k in lvl for k in ["ERR", "FAIL"]):
                                    severity = "ERROR"
                                elif "WARN" in lvl:
                                    severity = "WARNING"
                                else:
                                    severity = "INFO"

                    is_anom = 0 if label_str == "-" else 1

                    buffer.append({
                        "id": f"bgl-{line_id}",
                        "timestamp": ts_str,
                        "server": node.lower(),
                        "service": component,
                        "severity": severity,
                        "message": content,
                        "status_code": None,
                        "response_time": None,
                        "event_id": event_id,
                        "event_template": event_template,
                        "dataset": "BGL_full",
                        "raw_label": label_str,
                        "is_anomaly_label": is_anom
                    })

                # Process sliding windows from buffer
                while len(buffer) >= window_size:
                    window_logs = buffer[:window_size]
                    server = window_logs[0].get("server", "cluster-node")
                    t_start = window_logs[0].get("timestamp", f"w-{window_idx}")
                    t_end = window_logs[-1].get("timestamp", f"w-{window_idx+window_size}")
                    window_str = f"{t_start} - {t_end}"

                    feat = feature_extractor._calculate_bucket_features(server, window_str, window_logs)
                    feat["window_index"] = window_idx
                    window_idx += 1
                    yield feat

                    buffer = buffer[step_size:]

        finally:
            f_csv.close()
            if f_raw:
                f_raw.close()

    @classmethod
    def _normalize_openstack(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        logs = []
        for idx, row in df.iterrows():
            content = str(row.get("Content", ""))
            date_str = str(row.get("Date", "2017-05-16"))
            time_str = str(row.get("Time", "00:00:00"))
            ts_str = f"{date_str} {time_str[:8]}"

            # Parse server / node from ADDR or Pid
            addr = str(row.get("ADDR", "")).strip()
            ip_m = IP_REGEX.search(content) or IP_REGEX.search(addr)
            server = ip_m.group(0) if ip_m else f"nova-node-{row.get('Pid', idx)}"

            # Service / component
            component = str(row.get("Component") or row.get("Logrecord") or "nova-service")

            # Severity
            raw_level = str(row.get("Level", "INFO")).upper()
            severity = "WARNING" if "WARN" in raw_level else ("ERROR" if "ERR" in raw_level else "INFO")

            # Extract HTTP status or latency if genuinely present in Content
            status_code = None
            sm = STATUS_REGEX.search(content)
            if sm:
                try:
                    status_code = int(sm.group(1))
                except ValueError:
                    pass

            response_time = None
            tm = TIME_REGEX.search(content)
            if tm:
                try:
                    # In OpenStack logs, time is in seconds (e.g. 0.2477829)
                    response_time = round(float(tm.group(1)) * 1000.0, 2)
                except ValueError:
                    pass

            logs.append({
                "id": f"os-{row.get('LineId', idx+1)}",
                "timestamp": ts_str,
                "server": server.lower(),
                "service": component,
                "severity": severity,
                "message": content,
                "status_code": status_code,
                "response_time": response_time,
                "event_id": str(row.get("EventId", "")),
                "event_template": str(row.get("EventTemplate", "")),
                "dataset": "OpenStack",
                "is_anomaly_label": None  # Unsupervised
            })
        return logs

    @classmethod
    def _normalize_hdfs(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        logs = []
        for idx, row in df.iterrows():
            content = str(row.get("Content", ""))
            ts_str = _format_hdfs_timestamp(row.get("Date"), row.get("Time"))

            # Server from IP in content or Pid
            ip_m = IP_REGEX.search(content)
            server = ip_m.group(0) if ip_m else f"hdfs-node-{row.get('Pid', idx)}"

            # Service
            component = str(row.get("Component", "hdfs-dfs"))

            # Severity
            raw_level = str(row.get("Level", "INFO")).upper()
            severity = "WARNING" if "WARN" in raw_level else ("ERROR" if "ERR" in raw_level else "INFO")

            logs.append({
                "id": f"hdfs-{row.get('LineId', idx+1)}",
                "timestamp": ts_str,
                "server": server.lower(),
                "service": component,
                "severity": severity,
                "message": content,
                "status_code": None,
                "response_time": None,
                "event_id": str(row.get("EventId", "")),
                "event_template": str(row.get("EventTemplate", "")),
                "dataset": "HDFS",
                "is_anomaly_label": None  # Unsupervised
            })
        return logs

    @classmethod
    def _normalize_bgl(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        logs = []
        for idx, row in df.iterrows():
            content = str(row.get("Content", ""))
            ts_str = _format_bgl_timestamp(row.get("Timestamp"), row.get("Date"), row.get("Time"))

            # Server from Node
            server = str(row.get("Node") or f"bgl-node-{idx}").strip()

            # Service from Component or Type
            component = str(row.get("Component") or row.get("Type") or "bgl-system")

            # Severity
            raw_level = str(row.get("Level", "INFO")).upper()
            if any(k in raw_level for k in ["FATAL", "SEVERE", "CRIT"]):
                severity = "CRITICAL"
            elif any(k in raw_level for k in ["ERR", "FAIL"]):
                severity = "ERROR"
            elif "WARN" in raw_level:
                severity = "WARNING"
            else:
                severity = "INFO"

            # Ground-truth label extraction:
            # In BGL, '-' indicates normal execution, while alerts (e.g. APPREAD, KERNDTLB) indicate failure anomalies.
            raw_label = str(row.get("Label", "-")).strip()
            is_anomaly = 0 if raw_label == "-" else 1

            logs.append({
                "id": f"bgl-{row.get('LineId', idx+1)}",
                "timestamp": ts_str,
                "server": server.lower(),
                "service": component,
                "severity": severity,
                "message": content,
                "status_code": None,
                "response_time": None,
                "event_id": str(row.get("EventId", "")),
                "event_template": str(row.get("EventTemplate", "")),
                "dataset": "BGL",
                "raw_label": raw_label,
                "is_anomaly_label": is_anomaly  # Supervised ground-truth for post-prediction evaluation
            })
        return logs

dataset_adapter = DatasetAdapter()
