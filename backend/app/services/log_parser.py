import re
import csv
import json
import io
import uuid
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from backend.app.services.log_classifier import log_classifier

class LogParser:
    """
    Multi-format, fault-tolerant cloud log parser.
    Supports .log, .txt, .csv, and .json files.
    """

    IP_REGEX = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
    STATUS_CODE_REGEX = re.compile(r"\b(?:status[=:\s]+|HTTP[/\s\d.]*\s+)([1-5]\d\d)\b", re.IGNORECASE)
    RESPONSE_TIME_REGEX = re.compile(r"\b(?:latency|response_time|duration|took)[=:\s]+([0-9.]+)(?:ms|s)?\b", re.IGNORECASE)
    CPU_REGEX = re.compile(r"\b(?:cpu(?:_usage)?)[=:\s]+([0-9.]+)%?\b", re.IGNORECASE)
    MEMORY_REGEX = re.compile(r"\b(?:mem(?:ory)?(?:_usage)?)[=:\s]+([0-9.]+)%?\b", re.IGNORECASE)
    CORRELATION_REGEX = re.compile(r"\b(?:corr(?:elation)?_?id|trace_?id)[=:\s]+([a-zA-Z0-9_-]+)\b", re.IGNORECASE)

    # Standard bracketed log: 2026-09-07 14:22:04 [Server-03] [Database] ERROR: message
    BRACKETED_REGEX = re.compile(
        r"^(?:\[(?P<timestamp_b>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]|(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?))\s*"
        r"(?:\[(?P<server>[^\]]+)\]\s*)?"
        r"(?:\[(?P<service>[^\]]+)\]\s*)?"
        r"(?:(?P<severity>CRITICAL|ERROR|WARNING|WARN|INFO|DEBUG):?\s*)?"
        r"(?P<message>.*)$",
        re.IGNORECASE
    )

    # Key-Value log pattern: timestamp="..." server="..." service="..."
    KV_REGEX = re.compile(r'(\w+)=["\']?([^"\'\s]+)["\']?')

    @classmethod
    def parse_file(cls, filename: str, content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Parses uploaded file content according to its extension.
        Returns: (parsed_logs, list_of_errors)
        """
        fn = filename.lower()
        text = ""
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except Exception as e:
                return [], [f"Failed to decode file encoding: {str(e)}"]

        if fn.endswith(".json"):
            return cls.parse_json(text)
        elif fn.endswith(".csv"):
            return cls.parse_csv(text)
        else: # .log, .txt, or generic text
            return cls.parse_text_lines(text)

    @classmethod
    def parse_json(cls, text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        logs = []
        errors = []
        cleaned = text.strip()
        if not cleaned:
            return [], ["Empty JSON file."]

        # Attempt 1: Full JSON array or single object
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                data = [data]
            if isinstance(data, list):
                for i, item in enumerate(data):
                    try:
                        norm = cls._normalize_dict(item, line_num=i+1)
                        logs.append(norm)
                    except Exception as err:
                        errors.append(f"Record {i+1}: {str(err)}")
                return logs, errors
        except json.JSONDecodeError:
            # Attempt 2: JSON Lines (NDJSON)
            pass

        # Parse line by line as NDJSON
        for line_num, line in enumerate(cleaned.splitlines(), start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                item = json.loads(line_str)
                norm = cls._normalize_dict(item, line_num=line_num)
                logs.append(norm)
            except Exception as err:
                errors.append(f"Line {line_num}: JSON syntax error - {str(err)}")

        return logs, errors

    @classmethod
    def parse_csv(cls, text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        logs = []
        errors = []
        f = io.StringIO(text.strip())
        reader = csv.reader(f)
        try:
            header_row = next(reader, None)
        except Exception as e:
            return [], [f"Failed to read CSV header: {str(e)}"]

        if not header_row:
            return [], ["Empty CSV file."]

        # Map header columns to standard keys
        header_map = {}
        for idx, col in enumerate(header_row):
            c = col.strip().lower().replace(" ", "_")
            if c in {"timestamp", "time", "date", "datetime"}:
                header_map["timestamp"] = idx
            elif c in {"server", "host", "hostname", "node", "server_id"}:
                header_map["server"] = idx
            elif c in {"service", "app", "application", "component"}:
                header_map["service"] = idx
            elif c in {"severity", "level", "log_level", "type"}:
                header_map["severity"] = idx
            elif c in {"message", "msg", "log", "description", "event"}:
                header_map["message"] = idx
            elif c in {"ip", "ip_address", "client_ip", "source_ip"}:
                header_map["ip"] = idx
            elif c in {"status_code", "status", "http_status", "code"}:
                header_map["status_code"] = idx
            elif c in {"response_time", "latency", "latency_ms", "duration"}:
                header_map["response_time"] = idx
            elif c in {"cpu", "cpu_usage", "cpu_percent"}:
                header_map["cpu_usage"] = idx
            elif c in {"memory", "memory_usage", "mem_usage"}:
                header_map["memory_usage"] = idx
            elif c in {"correlation_id", "trace_id", "req_id", "request_id"}:
                header_map["correlation_id"] = idx

        for line_num, row in enumerate(reader, start=2):
            if not row or not any(row):
                continue
            try:
                raw_dict = {}
                for key, col_idx in header_map.items():
                    if col_idx < len(row):
                        raw_dict[key] = row[col_idx].strip()
                norm = cls._normalize_dict(raw_dict, line_num=line_num)
                logs.append(norm)
            except Exception as err:
                errors.append(f"Line {line_num}: {str(err)}")

        return logs, errors

    @classmethod
    def parse_text_lines(cls, text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        logs = []
        errors = []
        for line_num, line in enumerate(text.splitlines(), start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                norm = cls._parse_single_text_line(line_str, line_num)
                logs.append(norm)
            except Exception as err:
                errors.append(f"Line {line_num}: {str(err)}")
        return logs, errors

    @classmethod
    def _parse_single_text_line(cls, line: str, line_num: int) -> Dict[str, Any]:
        server = None
        service = None
        timestamp = None
        severity = None
        message = line

        # 1. Try bracketed format
        m = cls.BRACKETED_REGEX.match(line)
        if m:
            groups = m.groupdict()
            timestamp = groups.get("timestamp") or groups.get("timestamp_b")
            server = groups.get("server")
            service = groups.get("service")
            severity = groups.get("severity")
            message = groups.get("message") or line
        else:
            # 2. Try Key-Value format
            kvs = dict(cls.KV_REGEX.findall(line))
            if kvs:
                timestamp = kvs.get("time") or kvs.get("timestamp")
                server = kvs.get("server") or kvs.get("host")
                service = kvs.get("service") or kvs.get("app")
                severity = kvs.get("level") or kvs.get("severity")
                message = kvs.get("msg") or kvs.get("message") or line

        # Extract embedded telemetry
        ip = None
        ip_match = cls.IP_REGEX.search(line)
        if ip_match:
            ip = ip_match.group(0)

        status_code = None
        status_match = cls.STATUS_CODE_REGEX.search(line)
        if status_match:
            try:
                status_code = int(status_match.group(1))
            except ValueError:
                pass

        response_time = None
        rt_match = cls.RESPONSE_TIME_REGEX.search(line)
        if rt_match:
            try:
                response_time = float(rt_match.group(1))
            except ValueError:
                pass

        cpu_usage = None
        cpu_match = cls.CPU_REGEX.search(line)
        if cpu_match:
            try:
                cpu_usage = float(cpu_match.group(1))
            except ValueError:
                pass

        memory_usage = None
        mem_match = cls.MEMORY_REGEX.search(line)
        if mem_match:
            try:
                memory_usage = float(mem_match.group(1))
            except ValueError:
                pass

        corr_match = cls.CORRELATION_REGEX.search(line)
        correlation_id = corr_match.group(1) if corr_match else None

        raw = {
            "timestamp": timestamp,
            "server": server,
            "service": service,
            "severity": severity,
            "message": message,
            "ip": ip,
            "status_code": status_code,
            "response_time": response_time,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "correlation_id": correlation_id,
            "raw_text": line
        }
        return cls._normalize_dict(raw, line_num)

    @classmethod
    def _normalize_dict(cls, d: Dict[str, Any], line_num: int) -> Dict[str, Any]:
        # Generate stable ID
        log_id = str(d.get("id") or f"log-{uuid.uuid4().hex[:8]}")

        # Timestamp normalization
        raw_ts = d.get("timestamp") or d.get("time") or d.get("date")
        timestamp = cls._normalize_timestamp(raw_ts)

        # Server normalization (lowercase slug e.g. server-03)
        raw_server = str(d.get("server") or d.get("host") or d.get("node") or "server-01").strip().lower()
        if not raw_server.startswith("server-"):
            raw_server = f"server-{raw_server}" if not raw_server.isdigit() else f"server-{int(raw_server):02d}"

        # Service normalization
        raw_service = str(d.get("service") or d.get("app") or d.get("component") or "web-server").strip().lower()
        raw_service = raw_service.replace(" ", "-")

        # Message
        message = str(d.get("message") or d.get("msg") or d.get("raw_text") or "Log event recorded").strip()

        # Status Code
        status_code = None
        raw_sc = d.get("status_code") or d.get("status") or d.get("code")
        if raw_sc is not None and str(raw_sc).isdigit():
            status_code = int(raw_sc)

        # Response Time
        response_time = None
        raw_rt = d.get("response_time") or d.get("latency") or d.get("latency_ms") or d.get("duration")
        if raw_rt is not None:
            try:
                response_time = float(re.sub(r"[^\d.]", "", str(raw_rt)))
            except ValueError:
                pass

        # Severity Classification
        explicit_sev = d.get("severity") or d.get("level")
        severity = log_classifier.classify(message, explicit_severity=explicit_sev, status_code=status_code)

        # CPU & Memory
        cpu_usage = None
        if d.get("cpu_usage") is not None:
            try:
                cpu_usage = float(re.sub(r"[^\d.]", "", str(d["cpu_usage"])))
            except ValueError:
                pass

        memory_usage = None
        if d.get("memory_usage") is not None:
            try:
                memory_usage = float(re.sub(r"[^\d.]", "", str(d["memory_usage"])))
            except ValueError:
                pass

        ip = d.get("ip") or d.get("ip_address") or d.get("source_ip")
        if ip and not cls.IP_REGEX.search(str(ip)):
            ip = None

        correlation_id = d.get("correlation_id") or d.get("trace_id") or f"corr-{uuid.uuid4().hex[:6]}"

        return {
            "id": log_id,
            "timestamp": timestamp,
            "server": raw_server,
            "service": raw_service,
            "severity": severity,
            "message": message,
            "ip": ip,
            "ip_address": ip,
            "status_code": status_code,
            "response_time": response_time,
            "latency_ms": int(response_time) if response_time is not None else None,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "correlation_id": str(correlation_id),
            "environment": "production-aws",
            "stack_trace": d.get("stack_trace")
        }

    @classmethod
    def _normalize_timestamp(cls, raw_ts: Any) -> str:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not raw_ts:
            return now_str

        ts_str = str(raw_ts).strip()
        # Try common datetime formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y/%m/%d %H:%M:%S",
            "%d/%b/%Y:%H:%M:%S"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(ts_str.split("+")[0].split("Z")[0], fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        # If it's epoch timestamp
        try:
            val = float(ts_str)
            if val > 1e11: # milliseconds
                val = val / 1000.0
            dt = datetime.fromtimestamp(val)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            pass

        return now_str

log_parser = LogParser()
