from datetime import datetime, timedelta
import random

NOW = datetime.now()

def get_time_str(minutes_ago: int = 0) -> str:
    t = NOW - timedelta(minutes=minutes_ago)
    return t.strftime("%Y-%m-%d %H:%M:%S")

def get_iso_time(minutes_ago: int = 0) -> str:
    t = NOW - timedelta(minutes=minutes_ago)
    return t.isoformat()

# ---------------------------------------------------------
# SERVERS
# ---------------------------------------------------------
SERVERS = [
    {
        "id": "srv-01",
        "name": "Server-01",
        "ip": "10.0.1.14",
        "region": "us-east-1a",
        "status": "healthy",
        "cpu_usage": 34.2,
        "memory_usage": 58.1,
        "disk_usage": 42.0,
        "active_services": ["Web Server", "Reverse Proxy (Nginx)"],
        "last_ping": "1s ago"
    },
    {
        "id": "srv-02",
        "name": "Server-02",
        "ip": "10.0.1.28",
        "region": "us-east-1b",
        "status": "warning",
        "cpu_usage": 68.4,
        "memory_usage": 74.0,
        "disk_usage": 51.5,
        "active_services": ["Authentication", "OAuth2 Gateway"],
        "last_ping": "2s ago"
    },
    {
        "id": "srv-03",
        "name": "Server-03",
        "ip": "10.0.2.45",
        "region": "us-east-1c",
        "status": "critical",
        "cpu_usage": 96.8,
        "memory_usage": 91.2,
        "disk_usage": 79.4,
        "active_services": ["Database", "PostgreSQL Primary", "Payment API Pool"],
        "last_ping": "just now"
    },
    {
        "id": "srv-04",
        "name": "Server-04",
        "ip": "10.0.2.52",
        "region": "us-east-1a",
        "status": "healthy",
        "cpu_usage": 41.5,
        "memory_usage": 49.3,
        "disk_usage": 33.8,
        "active_services": ["Payment API", "Stripe Webhook Worker"],
        "last_ping": "3s ago"
    },
    {
        "id": "srv-05",
        "name": "Server-05",
        "ip": "10.0.3.11",
        "region": "us-east-1b",
        "status": "healthy",
        "cpu_usage": 22.0,
        "memory_usage": 62.7,
        "disk_usage": 28.1,
        "active_services": ["Cache", "Redis Master", "Session Store"],
        "last_ping": "1s ago"
    },
    {
        "id": "srv-06",
        "name": "Server-06",
        "ip": "10.0.3.19",
        "region": "us-east-1b",
        "status": "warning",
        "cpu_usage": 72.1,
        "memory_usage": 83.4,
        "disk_usage": 64.0,
        "active_services": ["Analytics Pipeline", "Log Forwarder"],
        "last_ping": "4s ago"
    }
]

# Adding 21 additional healthy cloud micro-nodes to represent total 27 servers (24 Healthy, 2 Warning, 1 Critical)
for i in range(7, 28):
    SERVERS.append({
        "id": f"srv-{i:02d}",
        "name": f"Server-{i:02d}",
        "ip": f"10.0.{(i % 4) + 1}.{10 + i}",
        "region": f"us-east-1{chr(97 + (i % 3))}",
        "status": "healthy",
        "cpu_usage": round(15.0 + (i * 1.5) % 35, 1),
        "memory_usage": round(30.0 + (i * 1.8) % 40, 1),
        "disk_usage": round(20.0 + (i * 1.2) % 30, 1),
        "active_services": ["Worker Node", "Internal Mesh"],
        "last_ping": "2s ago"
    })

# ---------------------------------------------------------
# INCIDENTS
# ---------------------------------------------------------
INCIDENTS = [
    {
        "id": "inc-01",
        "title": "Database Connectivity Failure",
        "severity": "Critical",
        "affected_server": "Server-03",
        "affected_service": "Payment API",
        "detected_at": get_time_str(2),
        "detected_relative": "2 min ago",
        "status": "Investigating",
        "related_events_count": 327,
        "ai_summary": "The system detected an abnormal increase in database connection failures. API response time also increased and payment requests began failing shortly afterward.",
        "evidence": [
            "327 database timeout events logged within a 4-minute window",
            "Error rate increased by 420% across Payment API endpoints",
            "API response latency increased by 63% (p99 spiked from 180ms to 4,200ms)",
            "Payment failure cascade directly followed connection pool depletion on PostgreSQL"
        ],
        "likely_root_cause": "Database connection exhaustion",
        "confidence": 91,
        "recommended_actions": [
            "Check database availability and active replication lag",
            "Check active connections using 'SELECT count(*) FROM pg_stat_activity'",
            "Check connection pool limits and max_connections parameters in pgbouncer/db config",
            "Review recent database changes or unindexed migration scripts deployed to Server-03"
        ],
        "timeline": [
            {
                "time": get_time_str(6),
                "server": "Server-03",
                "service": "Database",
                "event": "Active connections reached 99.4% threshold (497 / 500 connections in pool)",
                "severity": "WARNING"
            },
            {
                "time": get_time_str(4),
                "server": "Server-03",
                "service": "Database",
                "event": "psql: fatal: remaining connection slots are reserved for non-replication superuser connections",
                "severity": "CRITICAL"
            },
            {
                "time": get_time_str(3),
                "server": "Server-04",
                "service": "Payment API",
                "event": "HTTP 504 Gateway Timeout on POST /api/v1/checkout/process",
                "severity": "ERROR"
            },
            {
                "time": get_time_str(2),
                "server": "Server-03",
                "service": "Payment API",
                "event": "AI-CLAR correlated 327 related timeout logs & triggered automated incident alert",
                "severity": "CRITICAL"
            }
        ]
    },
    {
        "id": "inc-02",
        "title": "Suspicious Login Activity",
        "severity": "High",
        "affected_server": "Server-02",
        "affected_service": "Authentication",
        "detected_at": get_time_str(12),
        "detected_relative": "12 min ago",
        "status": "Open",
        "related_events_count": 47,
        "ai_summary": "47 consecutive failed authentication attempts were detected from an unrecognized external IP address targeting administrative SSH and user login endpoints.",
        "evidence": [
            "47 failed login attempts within 180 seconds",
            "Targeting common usernames: root, admin, cloud-user, devops",
            "Source IP geo-located outside standard organization whitelist: 198.51.100.42",
            "Zero successful handshakes completed during the burst"
        ],
        "likely_root_cause": "Distributed credential stuffing / automated brute-force attempt",
        "confidence": 88,
        "recommended_actions": [
            "Verify IP address reputation on AbuseIPDB or AWS WAF threat intel",
            "Apply immediate temporary firewall rule dropping ingress from 198.51.100.42",
            "Enforce MFA challenge on flagged user accounts",
            "Audit fail2ban and rate-limiting jail status on Server-02"
        ],
        "timeline": [
            {
                "time": get_time_str(15),
                "server": "Server-02",
                "service": "Authentication",
                "event": "PAM: 10 failed login attempts for user 'root' from 198.51.100.42",
                "severity": "WARNING"
            },
            {
                "time": get_time_str(13),
                "server": "Server-02",
                "service": "Authentication",
                "event": "PAM: Rapid burst exceeds 30 failed attempts across dictionary users",
                "severity": "ERROR"
            },
            {
                "time": get_time_str(12),
                "server": "Server-02",
                "service": "Authentication",
                "event": "Security heuristic triggered: Automated brute force attack classification",
                "severity": "HIGH"
            }
        ]
    },
    {
        "id": "inc-03",
        "title": "High CPU Usage & Thread Starvation",
        "severity": "Medium",
        "affected_server": "Server-01",
        "affected_service": "Web Server",
        "detected_at": get_time_str(20),
        "detected_relative": "20 min ago",
        "status": "Resolved",
        "related_events_count": 84,
        "ai_summary": "Sustained CPU spike to 98% caused by inefficient regex compilation on the product catalog search endpoint. Node cluster worker processes experienced thread starvation.",
        "evidence": [
            "CPU utilization exceeded 95% sustained threshold for 14 minutes",
            "Thread pool backlog queued 1,240 pending HTTP requests",
            "Worker respawn loop triggered twice by systemd supervisor"
        ],
        "likely_root_cause": "Catastrophic backtracking in search query regex parser",
        "confidence": 94,
        "recommended_actions": [
            "Deployed hotfix to replace regex parser with compiled linear automaton",
            "Restarted worker processes across Server-01 cluster",
            "Confirmed CPU utilization returned to normal 34% baseline"
        ],
        "timeline": [
            {
                "time": get_time_str(25),
                "server": "Server-01",
                "service": "Web Server",
                "event": "CPU load average increased from 1.4 to 8.2",
                "severity": "WARNING"
            },
            {
                "time": get_time_str(22),
                "server": "Server-01",
                "service": "Web Server",
                "event": "Request latency spiked to 3.8s on /api/search",
                "severity": "ERROR"
            },
            {
                "time": get_time_str(18),
                "server": "Server-01",
                "service": "Web Server",
                "event": "Mitigation applied: process restart and regex patch validated",
                "severity": "INFO"
            }
        ]
    }
]

# ---------------------------------------------------------
# ANOMALIES
# ---------------------------------------------------------
ANOMALIES = [
    {
        "id": "anom-01",
        "severity": "HIGH",
        "title": "Database Error Spike",
        "server": "Server-03",
        "service": "Payment API",
        "detection_time": get_time_str(2),
        "reason": "Error rate increased 420%",
        "confidence": 91,
        "status": "Active",
        "metric_name": "db_connection_timeouts_total",
        "baseline_value": "4 errors/min",
        "observed_value": "89 errors/min"
    },
    {
        "id": "anom-02",
        "severity": "HIGH",
        "title": "Abnormal Failed Auth Spike",
        "server": "Server-02",
        "service": "Authentication",
        "detection_time": get_time_str(12),
        "reason": "47 failed login attempts detected in 3 minutes",
        "confidence": 95,
        "status": "Investigating",
        "metric_name": "auth_failure_rate",
        "baseline_value": "0.2 failures/min",
        "observed_value": "15.6 failures/min"
    },
    {
        "id": "anom-03",
        "severity": "MEDIUM",
        "title": "CPU Usage Spike",
        "server": "Server-01",
        "service": "Web Server",
        "detection_time": get_time_str(24),
        "reason": "CPU utilization exceeded 95% threshold for 15m",
        "confidence": 89,
        "status": "Resolved",
        "metric_name": "system_cpu_percent",
        "baseline_value": "35%",
        "observed_value": "98%"
    },
    {
        "id": "anom-04",
        "severity": "MEDIUM",
        "title": "Abnormal Ingress Traffic",
        "server": "Server-06",
        "service": "Network",
        "detection_time": get_time_str(35),
        "reason": "Traffic surge 3.4x higher than standard Tuesday profile",
        "confidence": 84,
        "status": "Active",
        "metric_name": "network_rx_bytes_sec",
        "baseline_value": "120 Mbps",
        "observed_value": "408 Mbps"
    },
    {
        "id": "anom-05",
        "severity": "LOW",
        "title": "Cache Eviction Rate Elevation",
        "server": "Server-05",
        "service": "Cache (Redis)",
        "detection_time": get_time_str(55),
        "reason": "Key eviction velocity +48% above daily mean",
        "confidence": 78,
        "status": "Resolved",
        "metric_name": "redis_evicted_keys",
        "baseline_value": "12 keys/s",
        "observed_value": "24 keys/s"
    }
]

# ---------------------------------------------------------
# SECURITY EVENTS
# ---------------------------------------------------------
SECURITY_EVENTS = [
    {
        "id": "sec-01",
        "title": "Suspicious Login Activity",
        "server": "Server-02",
        "service": "Authentication",
        "timestamp": get_time_str(12),
        "source_ip": "198.51.100.42",
        "source_geo": "Frankfurt, Germany (AS24940)",
        "attempt_count": 47,
        "severity": "High",
        "risk_level": "High",
        "details": "47 failed SSH and API authentication attempts detected within 3 minutes targeting system administrator accounts.",
        "status": "Blocked",
        "action_taken": "Temporary rate-limit applied & IP added to suspicious watchlist"
    },
    {
        "id": "sec-02",
        "title": "Unauthorized Admin Path Traversal",
        "server": "Server-01",
        "service": "Web Server",
        "timestamp": get_time_str(48),
        "source_ip": "203.0.113.19",
        "source_geo": "São Paulo, Brazil (AS28573)",
        "attempt_count": 18,
        "severity": "Medium",
        "risk_level": "Medium",
        "details": "Repeated attempts to access sensitive paths '/.env', '/wp-admin', and '/debug/vars'.",
        "status": "Blocked",
        "action_taken": "HTTP 403 Forbidden issued & request blocked by edge WAF"
    },
    {
        "id": "sec-03",
        "title": "Expired JWT Replay Attempt",
        "server": "Server-04",
        "service": "Payment API",
        "timestamp": get_time_str(85),
        "source_ip": "192.0.2.88",
        "source_geo": "Virginia, USA (AWS EC2)",
        "attempt_count": 6,
        "severity": "Low",
        "risk_level": "Low",
        "details": "Client submitted expired cryptographic token with valid signature but timestamp older than 72 hours.",
        "status": "Monitored",
        "action_taken": "Token rejected with 401 Unauthorized; client session revoked"
    }
]

# ---------------------------------------------------------
# REALISTIC LOGS
# ---------------------------------------------------------
MOCK_LOGS = [
    {
        "id": "log-001",
        "timestamp": get_time_str(1),
        "server": "Server-03",
        "service": "Database",
        "severity": "CRITICAL",
        "message": "FATAL: remaining connection slots are reserved for non-replication superuser connections (max_connections=500)",
        "correlation_id": "corr-db-9842",
        "request_id": "req-89104",
        "latency_ms": 3200,
        "ip_address": "10.0.2.45",
        "environment": "production-aws",
        "stack_trace": "org.postgresql.util.PSQLException: FATAL: remaining connection slots are reserved\n  at org.postgresql.core.v3.ConnectionFactoryImpl.doAuthentication(ConnectionFactoryImpl.java:514)\n  at org.postgresql.core.v3.ConnectionFactoryImpl.tryConnect(ConnectionFactoryImpl.java:161)\n  at com.zaxxer.hikari.pool.PoolBase.newConnection(PoolBase.java:364)"
    },
    {
        "id": "log-002",
        "timestamp": get_time_str(2),
        "server": "Server-04",
        "service": "Payment API",
        "severity": "CRITICAL",
        "message": "Payment processing aborted: could not acquire database lease for transaction tx_992144",
        "correlation_id": "corr-db-9842",
        "request_id": "req-89105",
        "latency_ms": 4500,
        "ip_address": "10.0.2.52",
        "environment": "production-aws",
        "stack_trace": "TimeoutException: Database pool timeout after 5000ms\n  at com.cloud.payment.service.TransactionManager.process(TransactionManager.java:88)\n  at com.cloud.payment.controller.CheckoutController.checkout(CheckoutController.java:42)"
    },
    {
        "id": "log-003",
        "timestamp": get_time_str(2),
        "server": "Server-04",
        "service": "Payment API",
        "severity": "ERROR",
        "message": "HTTP 504 Gateway Timeout returned to client on POST /api/v1/payments/charge",
        "correlation_id": "corr-db-9842",
        "request_id": "req-89106",
        "latency_ms": 5012,
        "ip_address": "10.0.2.52",
        "environment": "production-aws"
    },
    {
        "id": "log-004",
        "timestamp": get_time_str(3),
        "server": "Server-03",
        "service": "Database",
        "severity": "ERROR",
        "message": "Connection pool HikariCP-1 failed to deliver connection in 30000ms. Active: 500, Idle: 0, Waiting: 48",
        "correlation_id": "corr-db-9842",
        "request_id": "req-89100",
        "latency_ms": 30000,
        "ip_address": "10.0.2.45",
        "environment": "production-aws"
    },
    {
        "id": "log-005",
        "timestamp": get_time_str(4),
        "server": "Server-03",
        "service": "Database",
        "severity": "WARNING",
        "message": "High memory consumption detected on worker thread backend_postgres_worker_42 (91.2% memory occupied)",
        "correlation_id": "corr-db-9842",
        "request_id": "req-89092",
        "latency_ms": 450,
        "ip_address": "10.0.2.45",
        "environment": "production-aws"
    },
    {
        "id": "log-006",
        "timestamp": get_time_str(5),
        "server": "Server-03",
        "service": "Database",
        "severity": "WARNING",
        "message": "Active connection pool count exceeded warning threshold 90% (452 / 500)",
        "correlation_id": "corr-db-9842",
        "request_id": "req-89080",
        "latency_ms": 120,
        "ip_address": "10.0.2.45",
        "environment": "production-aws"
    },
    {
        "id": "log-007",
        "timestamp": get_time_str(7),
        "server": "Server-01",
        "service": "Web Server",
        "severity": "INFO",
        "message": "Nginx upstream keepalive connection refreshed for backend pool us-east-1-pool-b",
        "correlation_id": "corr-web-1120",
        "request_id": "req-89071",
        "latency_ms": 12,
        "ip_address": "10.0.1.14",
        "environment": "production-aws"
    },
    {
        "id": "log-008",
        "timestamp": get_time_str(10),
        "server": "Server-02",
        "service": "Authentication",
        "severity": "WARNING",
        "message": "Failed password attempt for user 'admin' from 198.51.100.42 port 49202 ssh2",
        "correlation_id": "corr-sec-5541",
        "request_id": "req-89055",
        "latency_ms": 84,
        "ip_address": "198.51.100.42",
        "environment": "production-aws"
    },
    {
        "id": "log-009",
        "timestamp": get_time_str(11),
        "server": "Server-02",
        "service": "Authentication",
        "severity": "ERROR",
        "message": "Auth failure rate threshold triggered: 15 failed logins/min from subnet 198.51.100.0/24",
        "correlation_id": "corr-sec-5541",
        "request_id": "req-89048",
        "latency_ms": 110,
        "ip_address": "198.51.100.42",
        "environment": "production-aws"
    },
    {
        "id": "log-010",
        "timestamp": get_time_str(12),
        "server": "Server-02",
        "service": "Authentication",
        "severity": "CRITICAL",
        "message": "Potential brute-force pattern detected by AI-CLAR heuristic detector (Source IP: 198.51.100.42, attempts=47)",
        "correlation_id": "corr-sec-5541",
        "request_id": "req-89040",
        "latency_ms": 95,
        "ip_address": "198.51.100.42",
        "environment": "production-aws"
    },
    {
        "id": "log-011",
        "timestamp": get_time_str(15),
        "server": "Server-05",
        "service": "Cache",
        "severity": "INFO",
        "message": "Redis background save (BGSAVE) completed successfully in 340ms. 2,140,892 keys in RAM",
        "correlation_id": "corr-cache-3301",
        "request_id": "req-89020",
        "latency_ms": 340,
        "ip_address": "10.0.3.11",
        "environment": "production-aws"
    },
    {
        "id": "log-012",
        "timestamp": get_time_str(18),
        "server": "Server-01",
        "service": "Web Server",
        "severity": "INFO",
        "message": "HTTP 200 OK GET /healthz responded in 4ms from host Server-01",
        "correlation_id": "corr-health-0091",
        "request_id": "req-89002",
        "latency_ms": 4,
        "ip_address": "10.0.1.14",
        "environment": "production-aws"
    },
    {
        "id": "log-013",
        "timestamp": get_time_str(21),
        "server": "Server-01",
        "service": "Web Server",
        "severity": "ERROR",
        "message": "Worker thread event loop blocked for 4,210ms during complex JSON schema validation",
        "correlation_id": "corr-cpu-7782",
        "request_id": "req-88989",
        "latency_ms": 4210,
        "ip_address": "10.0.1.14",
        "environment": "production-aws"
    },
    {
        "id": "log-014",
        "timestamp": get_time_str(23),
        "server": "Server-01",
        "service": "Web Server",
        "severity": "WARNING",
        "message": "Node.js cluster worker 3 memory exceeded soft limit: 840MB / 1024MB",
        "correlation_id": "corr-cpu-7782",
        "request_id": "req-88975",
        "latency_ms": 15,
        "ip_address": "10.0.1.14",
        "environment": "production-aws"
    },
    {
        "id": "log-015",
        "timestamp": get_time_str(28),
        "server": "Server-06",
        "service": "Network",
        "severity": "WARNING",
        "message": "Interface eth0 packet buffer utilization reached 78% of ring capacity",
        "correlation_id": "corr-net-9912",
        "request_id": "req-88950",
        "latency_ms": 8,
        "ip_address": "10.0.3.19",
        "environment": "production-aws"
    },
    {
        "id": "log-016",
        "timestamp": get_time_str(32),
        "server": "Server-04",
        "service": "Payment API",
        "severity": "INFO",
        "message": "Payment gateway webhook acknowledged 200 OK (Event: charge.succeeded)",
        "correlation_id": "corr-pay-4412",
        "request_id": "req-88930",
        "latency_ms": 88,
        "ip_address": "10.0.2.52",
        "environment": "production-aws"
    },
    {
        "id": "log-017",
        "timestamp": get_time_str(38),
        "server": "Server-02",
        "service": "Authentication",
        "severity": "INFO",
        "message": "OAuth2 token refreshed successfully for client_id 'mobile-app-client'",
        "correlation_id": "corr-auth-1092",
        "request_id": "req-88910",
        "latency_ms": 42,
        "ip_address": "10.0.1.28",
        "environment": "production-aws"
    },
    {
        "id": "log-018",
        "timestamp": get_time_str(45),
        "server": "Server-05",
        "service": "Cache",
        "severity": "INFO",
        "message": "Cluster heartbeats acknowledged by 3 replica sentinels without quorum divergence",
        "correlation_id": "corr-cache-3302",
        "request_id": "req-88890",
        "latency_ms": 5,
        "ip_address": "10.0.3.11",
        "environment": "production-aws"
    },
    {
        "id": "log-019",
        "timestamp": get_time_str(50),
        "server": "Server-03",
        "service": "Database",
        "severity": "INFO",
        "message": "Autovacuum completed on table 'audit_events': 12,490 dead tuples cleaned",
        "correlation_id": "corr-db-9800",
        "request_id": "req-88870",
        "latency_ms": 2840,
        "ip_address": "10.0.2.45",
        "environment": "production-aws"
    },
    {
        "id": "log-020",
        "timestamp": get_time_str(58),
        "server": "Server-01",
        "service": "Web Server",
        "severity": "INFO",
        "message": "TLS handshake completed: TLSv1.3 ECDHE-RSA-AES256-GCM-SHA384",
        "correlation_id": "corr-web-1110",
        "request_id": "req-88850",
        "latency_ms": 18,
        "ip_address": "10.0.1.14",
        "environment": "production-aws"
    }
]

# Adding supplementary logs to provide realistic pagination & filtering
SERVICES = ["Authentication", "Payment API", "Database", "Web Server", "Network", "Cache"]
SEVERITIES = ["INFO", "INFO", "INFO", "WARNING", "INFO", "ERROR", "INFO"]
SERVERS_LIST = [f"Server-{i:02d}" for i in range(1, 10)]

for idx in range(21, 65):
    srv = random.choice(SERVERS_LIST)
    svc = random.choice(SERVICES)
    sev = random.choice(SEVERITIES)
    mins = idx * 2
    MOCK_LOGS.append({
        "id": f"log-{idx:03d}",
        "timestamp": get_time_str(mins),
        "server": srv,
        "service": svc,
        "severity": sev,
        "message": f"Service heartbeat routine checked {svc} on {srv}. Status code: 200, latency: {random.randint(8, 140)}ms",
        "correlation_id": f"corr-gen-{idx:04d}",
        "request_id": f"req-{80000 + idx}",
        "latency_ms": random.randint(10, 180),
        "ip_address": f"10.0.{(idx % 3) + 1}.{random.randint(10, 200)}",
        "environment": "production-aws"
    })

# ---------------------------------------------------------
# REPORTS
# ---------------------------------------------------------
REPORTS = [
    {
        "id": "rep-01",
        "incident_id": "inc-01",
        "title": "Post-Mortem: Database Connectivity Failure & Cascading Timeout",
        "severity": "Critical",
        "server": "Server-03",
        "service": "Payment API",
        "date": get_time_str(1),
        "status": "Generated",
        "summary": "At 14:21 UTC, Server-03 database connection pool exhausted all 500 allocated sockets due to an unindexed transaction query in the payment pipeline. This resulted in a 420% increase in error rates and 327 timeout events across Payment API services.",
        "likely_root_cause": "Database connection exhaustion caused by connection leak under surge traffic.",
        "impact_scope": "Payment API, Checkout funnel, PostgreSQL primary node.",
        "mitigation_steps": [
            "Increased pgbouncer max connection ceiling from 500 to 1,200",
            "Deployed hotfix to terminate idle transactions older than 30 seconds",
            "Added proactive alert rule at 85% connection pool saturation"
        ],
        "author": "AI-CLAR Automated RCA Engine"
    },
    {
        "id": "rep-02",
        "incident_id": "inc-02",
        "title": "Security Incident Brief: Brute Force Authentication Mitigation",
        "severity": "High",
        "server": "Server-02",
        "service": "Authentication",
        "date": get_time_str(10),
        "status": "Generated",
        "summary": "Automated brute-force assault detected originating from IP 198.51.100.42. 47 attempts were executed against SSH and user credentials within 3 minutes before threat containment.",
        "likely_root_cause": "External automated credential stuffing attack targeting administrative logins.",
        "impact_scope": "Server-02 Auth Gateway.",
        "mitigation_steps": [
            "Null-routed IP 198.51.100.42 at VPC edge security group",
            "Enforced strict 5-attempt rate-limiting on PAM SSH daemon",
            "Verified zero credentials were breached"
        ],
        "author": "AI-CLAR Security Auditor"
    },
    {
        "id": "rep-03",
        "incident_id": "inc-03",
        "title": "Performance Report: Web Server CPU Saturation Remediation",
        "severity": "Medium",
        "server": "Server-01",
        "service": "Web Server",
        "date": get_time_str(18),
        "status": "Archived",
        "summary": "High CPU utilization caused by unoptimized regex evaluation on /api/search. Node.js event loop latency exceeded SLA.",
        "likely_root_cause": "Catastrophic backtracking in user search string regex compiler.",
        "impact_scope": "Server-01 Web Server, Public Search API.",
        "mitigation_steps": [
            "Replaced regex parser with linear string-matching automaton",
            "Worker nodes restarted with zero dropped connections"
        ],
        "author": "AI-CLAR Automated RCA Engine"
    }
]

# ---------------------------------------------------------
# DASHBOARD STATS
# ---------------------------------------------------------
ACTIVITY_CHART_DATA = [
    {"time": "00:00", "requests": 2400, "errors": 12},
    {"time": "02:00", "requests": 1800, "errors": 8},
    {"time": "04:00", "requests": 1400, "errors": 5},
    {"time": "06:00", "requests": 2100, "errors": 9},
    {"time": "08:00", "requests": 3800, "errors": 22},
    {"time": "10:00", "requests": 5200, "errors": 35},
    {"time": "12:00", "requests": 6100, "errors": 48},
    {"time": "14:00", "requests": 5900, "errors": 327}, # Incident spike!
    {"time": "16:00", "requests": 6400, "errors": 89},
    {"time": "18:00", "requests": 5800, "errors": 42},
    {"time": "20:00", "requests": 4900, "errors": 28},
    {"time": "22:00", "requests": 3600, "errors": 16}
]

ERROR_TREND_DATA = [
    {"time": "13:00", "errors": 14, "baseline": 15},
    {"time": "13:20", "errors": 18, "baseline": 15},
    {"time": "13:40", "errors": 19, "baseline": 16},
    {"time": "14:00", "errors": 45, "baseline": 15},
    {"time": "14:10", "errors": 140, "baseline": 15},
    {"time": "14:20", "errors": 327, "baseline": 16}, # Peak spike
    {"time": "14:30", "errors": 185, "baseline": 16},
    {"time": "14:40", "errors": 88, "baseline": 15},
    {"time": "15:00", "errors": 34, "baseline": 15}
]

# ---------------------------------------------------------
# ASSISTANT PRE-BUILT INTENTS
# ---------------------------------------------------------
ASSISTANT_KNOWLEDGE = {
    "critical": {
        "answer": "There is currently 1 active CRITICAL incident:\n\n**Database Connectivity Failure** on **Server-03** affecting the **Payment API**.\n- Detected 2 minutes ago with **327 correlated timeout logs**.\n- Likely Root Cause: **Database connection exhaustion** (Confidence: 91%).\n- Recommended immediate action: Check active connections and increase connection pool limits.",
        "related_server": "Server-03",
        "related_incident_id": "inc-01",
        "confidence_score": 91,
        "evidence": [
            "327 timeout events in 4 minutes",
            "Error rate +420%",
            "Active connections reached 99.4% ceiling"
        ],
        "suggested_followups": [
            "Why did Server-03 fail?",
            "What caused the latest incident?",
            "Show recommended mitigation steps for Server-03"
        ]
    },
    "server-03": {
        "answer": "Analysis for **Server-03** (10.0.2.45, us-east-1c):\n\n- **Current Status**: Critical\n- **CPU**: 96.8% | **Memory**: 91.2%\n- **Failure Mechanism**: The PostgreSQL connection pool (HikariCP) reached maximum capacity (500/500 sockets), rejecting incoming requests from the Payment API.\n- **Related Logs**: 327 timeout events logged under correlation ID `corr-db-9842`.",
        "related_server": "Server-03",
        "related_incident_id": "inc-01",
        "confidence_score": 94,
        "evidence": [
            "psql: fatal: remaining connection slots reserved",
            "HikariCP-1 failed to deliver connection in 30000ms"
        ],
        "suggested_followups": [
            "What are today's critical errors?",
            "Generate incident report for Server-03",
            "Are there any security threats?"
        ]
    },
    "security": {
        "answer": "Security Status Overview:\n\n- **1 High Risk Alert**: Suspicious Login Activity detected on **Server-02** (Authentication service).\n- **Source IP**: 198.51.100.42 (Frankfurt, Germany).\n- **Attempt Count**: 47 failed authentication attempts targeting root and administrative accounts.\n- **Action Status**: Edge firewall rate-limiting applied. Zero compromised sessions detected.",
        "related_server": "Server-02",
        "related_incident_id": "inc-02",
        "confidence_score": 88,
        "evidence": [
            "47 failed SSH and PAM attempts within 180s",
            "Attack vector: Automated dictionary brute force"
        ],
        "suggested_followups": [
            "Which server has the most problems?",
            "Show full details for Server-02",
            "View security event audit log"
        ]
    },
    "problems": {
        "answer": "Server Problem Assessment:\n\n1. **Server-03 (Most problematic)**: Classified as **Critical**. Responsible for the active database pool failure and 327 errors.\n2. **Server-02**: Classified as **Warning** due to 47 brute-force authentication attempts.\n3. **Server-06**: Classified as **Warning** due to high ingress network buffer saturation (78%).\n\nThe remaining 24 cloud nodes are operating normally with average CPU below 40%.",
        "related_server": "Server-03",
        "related_incident_id": "inc-01",
        "confidence_score": 96,
        "evidence": [
            "Server-03 CPU at 96.8%, DB Pool at 100%",
            "Server-02 auth anomaly flagged",
            "24 servers healthy"
        ],
        "suggested_followups": [
            "Why did Server-03 fail?",
            "What are today's critical errors?",
            "Are there any security threats?"
        ]
    },
    "latest": {
        "answer": "The latest incident is **Database Connectivity Failure** (Incident ID: `inc-01`), detected 2 minutes ago on **Server-03**.\n\n- **Trigger**: Abnormal database timeout surge.\n- **Root Cause**: Database connection exhaustion.\n- **Confidence**: 91%\n- **Status**: Currently Investigating by DevOps team.",
        "related_server": "Server-03",
        "related_incident_id": "inc-01",
        "confidence_score": 91,
        "evidence": [
            "Spike from 4 to 89 errors/min",
            "Cascade to Payment API 504 responses"
        ],
        "suggested_followups": [
            "Why did Server-03 fail?",
            "Which server has the most problems?",
            "Generate incident report"
        ]
    }
}

# ---------------------------------------------------------
# ALERTS
# ---------------------------------------------------------
ALERTS = [
    {
        "alert_id": "alt-01",
        "incident_id": "inc-01",
        "title": "Database Connection Pool Exhaustion Alert",
        "severity": "CRITICAL",
        "message": "Critical incident detected on Server-03: Database Connection Pool Exhaustion affecting PostgreSQL Database.",
        "created_at": get_time_str(2),
        "read": False
    },
    {
        "alert_id": "alt-02",
        "incident_id": "inc-02",
        "title": "High Severity Security Anomaly Alert",
        "severity": "HIGH",
        "message": "Security threat detected on Server-02: Suspicious Login Activity / Brute Force Attack detected.",
        "created_at": get_time_str(15),
        "read": True
    }
]

