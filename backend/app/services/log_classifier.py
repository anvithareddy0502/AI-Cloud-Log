import re
from typing import Optional

class LogClassifier:
    """
    Contextual Severity Classification Service.
    Determines whether a log entry is INFO, WARNING, ERROR, or CRITICAL.
    Preserves explicit severity if present; infers using multi-keyword context if missing.
    """

    CRITICAL_PATTERNS = [
        r"service unavailable",
        r"database unavailable",
        r"system crash",
        r"multiple authentication failures",
        r"critical failure",
        r"connection slots are reserved",
        r"out of memory",
        r"\boom\b",
        r"kernel panic",
        r"fatal error",
        r"\bfatal\b",
        r"brute.?force",
        r"credential stuffing"
    ]

    ERROR_PATTERNS = [
        r"\bfailed\b",
        r"\bfailure\b",
        r"\bexception\b",
        r"\btimeout\b",
        r"timed?\s*out",
        r"time\s*out",
        r"connection refused",
        r"http 5\d\d",
        r"status:?\s*5\d\d",
        r"\b500\b",
        r"\b502\b",
        r"\b503\b",
        r"\b504\b",
        r"gateway timeout",
        r"internal server error",
        r"broken pipe",
        r"denied",
        r"aborted",
        r"\berror\b"
    ]

    WARNING_PATTERNS = [
        r"\bslow\b",
        r"high usage",
        r"\bretry\b",
        r"\bdeprecated\b",
        r"threshold exceeded",
        r"near capacity",
        r"high latency",
        r"exceeded warning threshold",
        r"memory consumption detected",
        r"http 4\d\d",
        r"\b401\b",
        r"\b403\b",
        r"\b404\b",
        r"unauthorized",
        r"forbidden",
        r"\bwarning\b",
        r"\bwarn\b"
    ]

    INFO_PATTERNS = [
        r"\bsuccessful\b",
        r"\bsuccess\b",
        r"\bstarted\b",
        r"\bcompleted\b",
        r"\bconnected\b",
        r"acknowledged",
        r"heartbeat",
        r"http 2\d\d",
        r"\b200\b",
        r"\b201\b",
        r"\b204\b",
        r"\bok\b",
        r"\binfo\b"
    ]

    @classmethod
    def classify(cls, message: str, explicit_severity: Optional[str] = None, status_code: Optional[int] = None) -> str:
        """
        Classifies log entry severity.
        """
        # 1. Respect explicit severity if valid
        if explicit_severity:
            norm = explicit_severity.strip().upper()
            if norm in {"CRITICAL", "FATAL"}:
                return "CRITICAL"
            elif norm in {"ERROR", "ERR"}:
                return "ERROR"
            elif norm in {"WARNING", "WARN"}:
                return "WARNING"
            elif norm in {"INFO", "DEBUG", "TRACE"}:
                return "INFO"

        msg_lower = (message or "").lower()

        # 2. Check HTTP status code if provided
        if status_code:
            if status_code >= 500:
                if "database" in msg_lower or "unavailable" in msg_lower or status_code == 503:
                    return "CRITICAL"
                return "ERROR"
            elif status_code in {401, 403, 429}:
                return "WARNING"

        # 3. Check Critical Patterns first
        for pat in cls.CRITICAL_PATTERNS:
            if re.search(pat, msg_lower):
                return "CRITICAL"

        # 4. Check Error Patterns
        for pat in cls.ERROR_PATTERNS:
            if re.search(pat, msg_lower):
                return "ERROR"

        # 5. Check Warning Patterns
        for pat in cls.WARNING_PATTERNS:
            if re.search(pat, msg_lower):
                return "WARNING"

        # 6. Default fallback to INFO
        return "INFO"

log_classifier = LogClassifier()
