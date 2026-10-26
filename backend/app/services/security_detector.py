import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.database.connection import db
from backend.app.utils.logger import logger

class RiskLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    ALL = [LOW, MEDIUM, HIGH, CRITICAL]

class SecurityEventStatus:
    ACTIVE = "ACTIVE"
    MITIGATED = "MITIGATED"
    REVIEWED = "REVIEWED"

class SecurityDetector:
    """
    Analyzes cloud logs for cyber-security anomalies, unauthorized ingress patterns,
    repeated credential brute-force attacks, and access violations.
    """

    FAILED_LOGIN_PATTERNS = [
        re.compile(r"failed (password|login|auth|authentication)", re.IGNORECASE),
        re.compile(r"authentication failure", re.IGNORECASE),
        re.compile(r"pam_unix.*authentication failure", re.IGNORECASE),
        re.compile(r"illegal user|invalid user", re.IGNORECASE),
        re.compile(r"invalid credentials", re.IGNORECASE)
    ]

    PERMISSION_DENIED_PATTERNS = [
        re.compile(r"permission denied", re.IGNORECASE),
        re.compile(r"access (denied|forbidden)", re.IGNORECASE),
        re.compile(r"insufficient (privileges|permissions)", re.IGNORECASE),
        re.compile(r"unauthorized role", re.IGNORECASE)
    ]

    def process_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyzes a batch of logs, generates security events for detected patterns,
        and saves them to the database.
        """
        if not logs:
            return []

        detected_events: List[Dict[str, Any]] = []

        # 1. Group logs by (server, source_ip)
        auth_failures: Dict[tuple, List[Dict[str, Any]]] = {}
        auth_401_403: Dict[tuple, List[Dict[str, Any]]] = {}
        perm_denials: Dict[tuple, List[Dict[str, Any]]] = {}
        ip_bursts: Dict[tuple, List[Dict[str, Any]]] = {}

        for l in logs:
            srv = str(l.get("server") or "server-01").strip()
            ip = str(l.get("ip") or l.get("ip_address") or l.get("source_ip") or "192.168.1.1").strip()
            msg = str(l.get("message") or "")
            code = int(l.get("status_code") or 0)
            key = (srv, ip)

            # Check Repeated Failed Logins
            if any(p.search(msg) for p in self.FAILED_LOGIN_PATTERNS):
                auth_failures.setdefault(key, []).append(l)

            # Check HTTP 401 / 403 Spikes
            if code in {401, 403} or ("401" in msg and "unauthorized" in msg.lower()) or ("403" in msg and "forbidden" in msg.lower()):
                auth_401_403.setdefault(key, []).append(l)

            # Check Permission Denied
            if any(p.search(msg) for p in self.PERMISSION_DENIED_PATTERNS):
                perm_denials.setdefault(key, []).append(l)

            # Track overall IP volume
            ip_bursts.setdefault(key, []).append(l)

        # 2. Evaluate Repeated Failed Logins
        for (srv, ip), group in auth_failures.items():
            count = len(group)
            if count >= 1:
                risk = RiskLevel.CRITICAL if count >= 10 else RiskLevel.HIGH if count >= 5 else RiskLevel.MEDIUM if count >= 3 else RiskLevel.LOW
                ts = str(group[0].get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
                evidence = (
                    f"{count} failed authentication attempt(s) detected on {srv} from source IP {ip}. "
                    f"Signature: '{group[0].get('message', '')}'."
                )
                sec_event = self._create_security_event(
                    timestamp=ts,
                    server=srv,
                    source_ip=ip,
                    event_type="Repeated Failed Logins",
                    attempt_count=count,
                    risk_level=risk,
                    evidence=evidence,
                    status=SecurityEventStatus.ACTIVE
                )
                detected_events.append(sec_event)

        # 3. Evaluate HTTP 401 / 403 Spikes
        for (srv, ip), group in auth_401_403.items():
            count = len(group)
            if count >= 2:
                risk = RiskLevel.CRITICAL if count >= 15 else RiskLevel.HIGH if count >= 6 else RiskLevel.MEDIUM
                ts = str(group[0].get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
                evidence = f"Spike of {count} unauthorized HTTP 401/403 responses originating from IP {ip} targeting {srv}."
                sec_event = self._create_security_event(
                    timestamp=ts,
                    server=srv,
                    source_ip=ip,
                    event_type="HTTP 401/403 Spike",
                    attempt_count=count,
                    risk_level=risk,
                    evidence=evidence,
                    status=SecurityEventStatus.ACTIVE
                )
                detected_events.append(sec_event)

        # 4. Evaluate Permission Denied Bursts
        for (srv, ip), group in perm_denials.items():
            count = len(group)
            if count >= 1:
                risk = RiskLevel.HIGH if count >= 3 else RiskLevel.MEDIUM
                ts = str(group[0].get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
                evidence = f"{count} permission denied access violation(s) recorded on {srv} from IP {ip}."
                sec_event = self._create_security_event(
                    timestamp=ts,
                    server=srv,
                    source_ip=ip,
                    event_type="Permission Denied Event",
                    attempt_count=count,
                    risk_level=risk,
                    evidence=evidence,
                    status=SecurityEventStatus.ACTIVE
                )
                detected_events.append(sec_event)

        # 5. Evaluate Unusual Request Bursts from single IP
        for (srv, ip), group in ip_bursts.items():
            count = len(group)
            if count >= 25:  # Rapid burst
                ts = str(group[0].get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
                evidence = f"High-velocity request burst of {count} events detected from single IP {ip} targeting {srv}."
                sec_event = self._create_security_event(
                    timestamp=ts,
                    server=srv,
                    source_ip=ip,
                    event_type="Unusual Source IP Activity",
                    attempt_count=count,
                    risk_level=RiskLevel.MEDIUM if count < 50 else RiskLevel.HIGH,
                    evidence=evidence,
                    status=SecurityEventStatus.ACTIVE
                )
                detected_events.append(sec_event)

        return detected_events

    def _create_security_event(
        self,
        timestamp: str,
        server: str,
        source_ip: str,
        event_type: str,
        attempt_count: int,
        risk_level: str,
        evidence: str,
        status: str
    ) -> Dict[str, Any]:
        now_ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        doc_id = f"sec-{now_ts}-{source_ip.replace('.', '')[-4:]}"
        
        doc = {
            "id": doc_id,
            "timestamp": timestamp,
            "server": server,
            "source_ip": source_ip,
            "event_type": event_type,
            "attempt_count": attempt_count,
            "risk_level": risk_level,
            "evidence": evidence,
            "status": status,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Upsert or insert into db.security_events
        existing = db.security_events.find_one({
            "server": server,
            "source_ip": source_ip,
            "event_type": event_type,
            "status": SecurityEventStatus.ACTIVE
        })
        
        if existing:
            # Update existing event with higher attempt count and evidence
            new_count = existing.get("attempt_count", 0) + attempt_count
            updated_fields = {
                "attempt_count": new_count,
                "evidence": f"{new_count} attempts recorded: {evidence}",
                "timestamp": timestamp,
                "risk_level": RiskLevel.CRITICAL if new_count >= 10 else RiskLevel.HIGH if new_count >= 5 else existing.get("risk_level", RiskLevel.MEDIUM)
            }
            db.security_events.update_one({"id": existing["id"]}, {"$set": updated_fields})
            return {**existing, **updated_fields}
        else:
            db.security_events.insert_one(doc)
            logger.info("Created Security Event '%s' [%s] on %s from %s (Count: %d)", event_type, risk_level, server, source_ip, attempt_count)
            return doc

    def detect_security_events(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self.process_logs(logs)

security_detector = SecurityDetector()
