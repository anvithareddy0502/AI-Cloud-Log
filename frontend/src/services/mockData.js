// Frontend synchronous mock data fallback
export const MOCK_SERVERS = [
  {
    id: "srv-01",
    name: "Server-01",
    ip: "10.0.1.14",
    region: "us-east-1a",
    status: "healthy",
    cpu_usage: 34.2,
    memory_usage: 58.1,
    disk_usage: 42.0,
    active_services: ["Web Server", "Reverse Proxy (Nginx)"],
    last_ping: "1s ago"
  },
  {
    id: "srv-02",
    name: "Server-02",
    ip: "10.0.1.28",
    region: "us-east-1b",
    status: "warning",
    cpu_usage: 68.4,
    memory_usage: 74.0,
    disk_usage: 51.5,
    active_services: ["Authentication", "OAuth2 Gateway"],
    last_ping: "2s ago"
  },
  {
    id: "srv-03",
    name: "Server-03",
    ip: "10.0.2.45",
    region: "us-east-1c",
    status: "critical",
    cpu_usage: 96.8,
    memory_usage: 91.2,
    disk_usage: 79.4,
    active_services: ["Database", "PostgreSQL Primary", "Payment API Pool"],
    last_ping: "just now"
  },
  {
    id: "srv-04",
    name: "Server-04",
    ip: "10.0.2.52",
    region: "us-east-1a",
    status: "healthy",
    cpu_usage: 41.5,
    memory_usage: 49.3,
    disk_usage: 33.8,
    active_services: ["Payment API", "Stripe Webhook Worker"],
    last_ping: "3s ago"
  },
  {
    id: "srv-05",
    name: "Server-05",
    ip: "10.0.3.11",
    region: "us-east-1b",
    status: "healthy",
    cpu_usage: 22.0,
    memory_usage: 62.7,
    disk_usage: 28.1,
    active_services: ["Cache", "Redis Master", "Session Store"],
    last_ping: "1s ago"
  },
  {
    id: "srv-06",
    name: "Server-06",
    ip: "10.0.3.19",
    region: "us-east-1b",
    status: "warning",
    cpu_usage: 72.1,
    memory_usage: 83.4,
    disk_usage: 64.0,
    active_services: ["Analytics Pipeline", "Log Forwarder"],
    last_ping: "4s ago"
  }
];

export const MOCK_INCIDENTS = [
  {
    id: "inc-01",
    title: "Database Connectivity Failure",
    severity: "Critical",
    affected_server: "Server-03",
    affected_service: "Payment API",
    detected_at: "2026-09-07 14:21:00",
    detected_relative: "2 min ago",
    status: "Investigating",
    related_events_count: 327,
    ai_summary: "The system detected an abnormal increase in database connection failures. API response time also increased and payment requests began failing shortly afterward.",
    evidence: [
      "327 database timeout events logged within a 4-minute window",
      "Error rate increased by 420% across Payment API endpoints",
      "API response latency increased by 63% (p99 spiked from 180ms to 4,200ms)",
      "Payment failure cascade directly followed connection pool depletion on PostgreSQL"
    ],
    likely_root_cause: "Database connection exhaustion",
    confidence: 91,
    recommended_actions: [
      "Check database availability and active replication lag",
      "Check active connections using 'SELECT count(*) FROM pg_stat_activity'",
      "Check connection pool limits and max_connections parameters in pgbouncer/db config",
      "Review recent database changes or unindexed migration scripts deployed to Server-03"
    ],
    timeline: [
      {
        time: "14:19:12",
        server: "Server-03",
        service: "Database",
        event: "Active connections reached 99.4% threshold (497 / 500 connections in pool)",
        severity: "WARNING"
      },
      {
        time: "14:20:04",
        server: "Server-03",
        service: "Database",
        event: "psql: fatal: remaining connection slots are reserved for non-replication superuser connections",
        severity: "CRITICAL"
      },
      {
        time: "14:20:45",
        server: "Server-04",
        service: "Payment API",
        event: "HTTP 504 Gateway Timeout on POST /api/v1/checkout/process",
        severity: "ERROR"
      },
      {
        time: "14:21:00",
        server: "Server-03",
        service: "Payment API",
        event: "AI-CLAR correlated 327 related timeout logs & triggered automated incident alert",
        severity: "CRITICAL"
      }
    ]
  },
  {
    id: "inc-02",
    title: "Suspicious Login Activity",
    severity: "High",
    affected_server: "Server-02",
    affected_service: "Authentication",
    detected_at: "2026-09-07 14:11:00",
    detected_relative: "12 min ago",
    status: "Open",
    related_events_count: 47,
    ai_summary: "47 consecutive failed authentication attempts were detected from an unrecognized external IP address targeting administrative SSH and user login endpoints.",
    evidence: [
      "47 failed login attempts within 180 seconds",
      "Targeting common usernames: root, admin, cloud-user, devops",
      "Source IP geo-located outside standard organization whitelist: 198.51.100.42",
      "Zero successful handshakes completed during the burst"
    ],
    likely_root_cause: "Distributed credential stuffing / automated brute-force attempt",
    confidence: 88,
    recommended_actions: [
      "Verify IP address reputation on AbuseIPDB or AWS WAF threat intel",
      "Apply immediate temporary firewall rule dropping ingress from 198.51.100.42",
      "Enforce MFA challenge on flagged user accounts",
      "Audit fail2ban and rate-limiting jail status on Server-02"
    ],
    timeline: [
      {
        time: "14:08:15",
        server: "Server-02",
        service: "Authentication",
        event: "PAM: 10 failed login attempts for user 'root' from 198.51.100.42",
        severity: "WARNING"
      },
      {
        time: "14:10:22",
        server: "Server-02",
        service: "Authentication",
        event: "PAM: Rapid burst exceeds 30 failed attempts across dictionary users",
        severity: "ERROR"
      },
      {
        time: "14:11:00",
        server: "Server-02",
        service: "Authentication",
        event: "Security heuristic triggered: Automated brute force attack classification",
        severity: "HIGH"
      }
    ]
  },
  {
    id: "inc-03",
    title: "High CPU Usage",
    severity: "Medium",
    affected_server: "Server-01",
    affected_service: "Web Server",
    detected_at: "2026-09-07 14:03:00",
    detected_relative: "20 min ago",
    status: "Resolved",
    related_events_count: 84,
    ai_summary: "Sustained CPU spike to 98% caused by inefficient regex compilation on the product catalog search endpoint. Node cluster worker processes experienced thread starvation.",
    evidence: [
      "CPU utilization exceeded 95% sustained threshold for 14 minutes",
      "Thread pool backlog queued 1,240 pending HTTP requests",
      "Worker respawn loop triggered twice by systemd supervisor"
    ],
    likely_root_cause: "Catastrophic backtracking in search query regex parser",
    confidence: 94,
    recommended_actions: [
      "Deployed hotfix to replace regex parser with compiled linear automaton",
      "Restarted worker processes across Server-01 cluster",
      "Confirmed CPU utilization returned to normal 34% baseline"
    ],
    timeline: [
      {
        time: "13:58:30",
        server: "Server-01",
        service: "Web Server",
        event: "CPU load average increased from 1.4 to 8.2",
        severity: "WARNING"
      },
      {
        time: "14:01:10",
        server: "Server-01",
        service: "Web Server",
        event: "Request latency spiked to 3.8s on /api/search",
        severity: "ERROR"
      },
      {
        time: "14:03:00",
        server: "Server-01",
        service: "Web Server",
        event: "Mitigation applied: process restart and regex patch validated",
        severity: "INFO"
      }
    ]
  }
];

export const MOCK_ANOMALIES = [
  {
    id: "anom-01",
    severity: "HIGH",
    title: "Database Error Spike",
    server: "Server-03",
    service: "Payment API",
    detection_time: "2 min ago",
    reason: "Error rate increased 420%",
    confidence: 91,
    status: "Active",
    metric_name: "db_connection_timeouts_total",
    baseline_value: "4 errors/min",
    observed_value: "89 errors/min"
  },
  {
    id: "anom-02",
    severity: "HIGH",
    title: "Abnormal Failed Auth Spike",
    server: "Server-02",
    service: "Authentication",
    detection_time: "12 min ago",
    reason: "47 failed login attempts detected in 3 minutes",
    confidence: 95,
    status: "Investigating",
    metric_name: "auth_failure_rate",
    baseline_value: "0.2 failures/min",
    observed_value: "15.6 failures/min"
  },
  {
    id: "anom-03",
    severity: "MEDIUM",
    title: "CPU Usage Spike",
    server: "Server-01",
    service: "Web Server",
    detection_time: "24 min ago",
    reason: "CPU utilization exceeded 95% threshold for 15m",
    confidence: 89,
    status: "Resolved",
    metric_name: "system_cpu_percent",
    baseline_value: "35%",
    observed_value: "98%"
  },
  {
    id: "anom-04",
    severity: "MEDIUM",
    title: "Abnormal Ingress Traffic",
    server: "Server-06",
    service: "Network",
    detection_time: "35 min ago",
    reason: "Traffic surge 3.4x higher than standard Tuesday profile",
    confidence: 84,
    status: "Active",
    metric_name: "network_rx_bytes_sec",
    baseline_value: "120 Mbps",
    observed_value: "408 Mbps"
  },
  {
    id: "anom-05",
    severity: "LOW",
    title: "Cache Eviction Rate Elevation",
    server: "Server-05",
    service: "Cache (Redis)",
    detection_time: "55 min ago",
    reason: "Key eviction velocity +48% above daily mean",
    confidence: 78,
    status: "Resolved",
    metric_name: "redis_evicted_keys",
    baseline_value: "12 keys/s",
    observed_value: "24 keys/s"
  }
];

export const MOCK_SECURITY_EVENTS = [
  {
    id: "sec-01",
    title: "Suspicious Login Activity",
    server: "Server-02",
    service: "Authentication",
    timestamp: "12 min ago",
    source_ip: "198.51.100.42",
    source_geo: "Frankfurt, Germany (AS24940)",
    attempt_count: 47,
    severity: "High",
    risk_level: "High",
    details: "47 failed SSH and API authentication attempts detected within 3 minutes targeting system administrator accounts.",
    status: "Blocked",
    action_taken: "Temporary rate-limit applied & IP added to suspicious watchlist"
  },
  {
    id: "sec-02",
    title: "Unauthorized Admin Path Traversal",
    server: "Server-01",
    service: "Web Server",
    timestamp: "48 min ago",
    source_ip: "203.0.113.19",
    source_geo: "São Paulo, Brazil (AS28573)",
    attempt_count: 18,
    severity: "Medium",
    risk_level: "Medium",
    details: "Repeated attempts to access sensitive paths '/.env', '/wp-admin', and '/debug/vars'.",
    status: "Blocked",
    action_taken: "HTTP 403 Forbidden issued & request blocked by edge WAF"
  },
  {
    id: "sec-03",
    title: "Expired JWT Replay Attempt",
    server: "Server-04",
    service: "Payment API",
    timestamp: "1 hour ago",
    source_ip: "192.0.2.88",
    source_geo: "Virginia, USA (AWS EC2)",
    attempt_count: 6,
    severity: "Low",
    risk_level: "Low",
    details: "Client submitted expired cryptographic token with valid signature but timestamp older than 72 hours.",
    status: "Monitored",
    action_taken: "Token rejected with 401 Unauthorized; client session revoked"
  }
];

export const MOCK_LOGS_LIST = [
  {
    id: "log-001",
    timestamp: "2026-09-07 14:22:04",
    server: "Server-03",
    service: "Database",
    severity: "CRITICAL",
    message: "FATAL: remaining connection slots are reserved for non-replication superuser connections (max_connections=500)",
    correlation_id: "corr-db-9842",
    request_id: "req-89104",
    latency_ms: 3200,
    ip_address: "10.0.2.45",
    environment: "production-aws",
    stack_trace: "org.postgresql.util.PSQLException: FATAL: remaining connection slots are reserved\n  at org.postgresql.core.v3.ConnectionFactoryImpl.doAuthentication(ConnectionFactoryImpl.java:514)\n  at org.postgresql.core.v3.ConnectionFactoryImpl.tryConnect(ConnectionFactoryImpl.java:161)\n  at com.zaxxer.hikari.pool.PoolBase.newConnection(PoolBase.java:364)"
  },
  {
    id: "log-002",
    timestamp: "2026-09-07 14:21:45",
    server: "Server-04",
    service: "Payment API",
    severity: "CRITICAL",
    message: "Payment processing aborted: could not acquire database lease for transaction tx_992144",
    correlation_id: "corr-db-9842",
    request_id: "req-89105",
    latency_ms: 4500,
    ip_address: "10.0.2.52",
    environment: "production-aws",
    stack_trace: "TimeoutException: Database pool timeout after 5000ms\n  at com.cloud.payment.service.TransactionManager.process(TransactionManager.java:88)\n  at com.cloud.payment.controller.CheckoutController.checkout(CheckoutController.java:42)"
  },
  {
    id: "log-003",
    timestamp: "2026-09-07 14:21:30",
    server: "Server-04",
    service: "Payment API",
    severity: "ERROR",
    message: "HTTP 504 Gateway Timeout returned to client on POST /api/v1/payments/charge",
    correlation_id: "corr-db-9842",
    request_id: "req-89106",
    latency_ms: 5012,
    ip_address: "10.0.2.52",
    environment: "production-aws"
  },
  {
    id: "log-004",
    timestamp: "2026-09-07 14:20:18",
    server: "Server-03",
    service: "Database",
    severity: "ERROR",
    message: "Connection pool HikariCP-1 failed to deliver connection in 30000ms. Active: 500, Idle: 0, Waiting: 48",
    correlation_id: "corr-db-9842",
    request_id: "req-89100",
    latency_ms: 30000,
    ip_address: "10.0.2.45",
    environment: "production-aws"
  },
  {
    id: "log-005",
    timestamp: "2026-09-07 14:18:50",
    server: "Server-03",
    service: "Database",
    severity: "WARNING",
    message: "High memory consumption detected on worker thread backend_postgres_worker_42 (91.2% memory occupied)",
    correlation_id: "corr-db-9842",
    request_id: "req-89092",
    latency_ms: 450,
    ip_address: "10.0.2.45",
    environment: "production-aws"
  },
  {
    id: "log-006",
    timestamp: "2026-09-07 14:17:15",
    server: "Server-03",
    service: "Database",
    severity: "WARNING",
    message: "Active connection pool count exceeded warning threshold 90% (452 / 500)",
    correlation_id: "corr-db-9842",
    request_id: "req-89080",
    latency_ms: 120,
    ip_address: "10.0.2.45",
    environment: "production-aws"
  },
  {
    id: "log-007",
    timestamp: "2026-09-07 14:15:20",
    server: "Server-01",
    service: "Web Server",
    severity: "INFO",
    message: "Nginx upstream keepalive connection refreshed for backend pool us-east-1-pool-b",
    correlation_id: "corr-web-1120",
    request_id: "req-89071",
    latency_ms: 12,
    ip_address: "10.0.1.14",
    environment: "production-aws"
  },
  {
    id: "log-008",
    timestamp: "2026-09-07 14:12:44",
    server: "Server-02",
    service: "Authentication",
    severity: "WARNING",
    message: "Failed password attempt for user 'admin' from 198.51.100.42 port 49202 ssh2",
    correlation_id: "corr-sec-5541",
    request_id: "req-89055",
    latency_ms: 84,
    ip_address: "198.51.100.42",
    environment: "production-aws"
  },
  {
    id: "log-009",
    timestamp: "2026-09-07 14:11:30",
    server: "Server-02",
    service: "Authentication",
    severity: "ERROR",
    message: "Auth failure rate threshold triggered: 15 failed logins/min from subnet 198.51.100.0/24",
    correlation_id: "corr-sec-5541",
    request_id: "req-89048",
    latency_ms: 110,
    ip_address: "198.51.100.42",
    environment: "production-aws"
  },
  {
    id: "log-010",
    timestamp: "2026-09-07 14:11:00",
    server: "Server-02",
    service: "Authentication",
    severity: "CRITICAL",
    message: "Potential brute-force pattern detected by AI-CLAR heuristic detector (Source IP: 198.51.100.42, attempts=47)",
    correlation_id: "corr-sec-5541",
    request_id: "req-89040",
    latency_ms: 95,
    ip_address: "198.51.100.42",
    environment: "production-aws"
  },
  {
    id: "log-011",
    timestamp: "2026-09-07 14:05:10",
    server: "Server-05",
    service: "Cache",
    severity: "INFO",
    message: "Redis background save (BGSAVE) completed successfully in 340ms. 2,140,892 keys in RAM",
    correlation_id: "corr-cache-3301",
    request_id: "req-89020",
    latency_ms: 340,
    ip_address: "10.0.3.11",
    environment: "production-aws"
  },
  {
    id: "log-012",
    timestamp: "2026-09-07 14:03:00",
    server: "Server-01",
    service: "Web Server",
    severity: "INFO",
    message: "HTTP 200 OK GET /healthz responded in 4ms from host Server-01",
    correlation_id: "corr-health-0091",
    request_id: "req-89002",
    latency_ms: 4,
    ip_address: "10.0.1.14",
    environment: "production-aws"
  },
  {
    id: "log-013",
    timestamp: "2026-09-07 13:58:20",
    server: "Server-01",
    service: "Web Server",
    severity: "ERROR",
    message: "Worker thread event loop blocked for 4,210ms during complex JSON schema validation",
    correlation_id: "corr-cpu-7782",
    request_id: "req-88989",
    latency_ms: 4210,
    ip_address: "10.0.1.14",
    environment: "production-aws"
  },
  {
    id: "log-014",
    timestamp: "2026-09-07 13:55:00",
    server: "Server-01",
    service: "Web Server",
    severity: "WARNING",
    message: "Node.js cluster worker 3 memory exceeded soft limit: 840MB / 1024MB",
    correlation_id: "corr-cpu-7782",
    request_id: "req-88975",
    latency_ms: 15,
    ip_address: "10.0.1.14",
    environment: "production-aws"
  },
  {
    id: "log-015",
    timestamp: "2026-09-07 13:48:12",
    server: "Server-06",
    service: "Network",
    severity: "WARNING",
    message: "Interface eth0 packet buffer utilization reached 78% of ring capacity",
    correlation_id: "corr-net-9912",
    request_id: "req-88950",
    latency_ms: 8,
    ip_address: "10.0.3.19",
    environment: "production-aws"
  },
  {
    id: "log-016",
    timestamp: "2026-09-07 13:40:05",
    server: "Server-04",
    service: "Payment API",
    severity: "INFO",
    message: "Payment gateway webhook acknowledged 200 OK (Event: charge.succeeded)",
    correlation_id: "corr-pay-4412",
    request_id: "req-88930",
    latency_ms: 88,
    ip_address: "10.0.2.52",
    environment: "production-aws"
  },
  {
    id: "log-017",
    timestamp: "2026-09-07 13:30:19",
    server: "Server-02",
    service: "Authentication",
    severity: "INFO",
    message: "OAuth2 token refreshed successfully for client_id 'mobile-app-client'",
    correlation_id: "corr-auth-1092",
    request_id: "req-88910",
    latency_ms: 42,
    ip_address: "10.0.1.28",
    environment: "production-aws"
  },
  {
    id: "log-018",
    timestamp: "2026-09-07 13:20:00",
    server: "Server-05",
    service: "Cache",
    severity: "INFO",
    message: "Cluster heartbeats acknowledged by 3 replica sentinels without quorum divergence",
    correlation_id: "corr-cache-3302",
    request_id: "req-88890",
    latency_ms: 5,
    ip_address: "10.0.3.11",
    environment: "production-aws"
  },
  {
    id: "log-019",
    timestamp: "2026-09-07 13:10:44",
    server: "Server-03",
    service: "Database",
    severity: "INFO",
    message: "Autovacuum completed on table 'audit_events': 12,490 dead tuples cleaned",
    correlation_id: "corr-db-9800",
    request_id: "req-88870",
    latency_ms: 2840,
    ip_address: "10.0.2.45",
    environment: "production-aws"
  },
  {
    id: "log-020",
    timestamp: "2026-09-07 13:00:15",
    server: "Server-01",
    service: "Web Server",
    severity: "INFO",
    message: "TLS handshake completed: TLSv1.3 ECDHE-RSA-AES256-GCM-SHA384",
    correlation_id: "corr-web-1110",
    request_id: "req-88850",
    latency_ms: 18,
    ip_address: "10.0.1.14",
    environment: "production-aws"
  }
];

export const MOCK_REPORTS = [
  {
    id: "rep-01",
    incident_id: "inc-01",
    title: "Post-Mortem: Database Connectivity Failure & Cascading Timeout",
    severity: "Critical",
    server: "Server-03",
    service: "Payment API",
    date: "2026-09-07 14:24:00",
    status: "Generated",
    summary: "At 14:21 UTC, Server-03 database connection pool exhausted all 500 allocated sockets due to an unindexed transaction query in the payment pipeline. This resulted in a 420% increase in error rates and 327 timeout events across Payment API services.",
    likely_root_cause: "Database connection exhaustion caused by connection leak under surge traffic.",
    impact_scope: "Payment API, Checkout funnel, PostgreSQL primary node.",
    mitigation_steps: [
      "Increased pgbouncer max connection ceiling from 500 to 1,200",
      "Deployed hotfix to terminate idle transactions older than 30 seconds",
      "Added proactive alert rule at 85% connection pool saturation"
    ],
    author: "AI-CLAR Automated RCA Engine"
  },
  {
    id: "rep-02",
    incident_id: "inc-02",
    title: "Security Incident Brief: Brute Force Authentication Mitigation",
    severity: "High",
    server: "Server-02",
    service: "Authentication",
    date: "2026-09-07 14:15:00",
    status: "Generated",
    summary: "Automated brute-force assault detected originating from IP 198.51.100.42. 47 attempts were executed against SSH and user credentials within 3 minutes before threat containment.",
    likely_root_cause: "External automated credential stuffing attack targeting administrative logins.",
    impact_scope: "Server-02 Auth Gateway.",
    mitigation_steps: [
      "Null-routed IP 198.51.100.42 at VPC edge security group",
      "Enforced strict 5-attempt rate-limiting on PAM SSH daemon",
      "Verified zero credentials were breached"
    ],
    author: "AI-CLAR Security Auditor"
  },
  {
    id: "rep-03",
    incident_id: "inc-03",
    title: "Performance Report: Web Server CPU Saturation Remediation",
    severity: "Medium",
    server: "Server-01",
    service: "Web Server",
    date: "2026-09-07 14:05:00",
    status: "Archived",
    summary: "High CPU utilization caused by unoptimized regex evaluation on /api/search. Node.js event loop latency exceeded SLA.",
    likely_root_cause: "Catastrophic backtracking in user search string regex compiler.",
    impact_scope: "Server-01 Web Server, Public Search API.",
    mitigation_steps: [
      "Replaced regex parser with linear string-matching automaton",
      "Worker nodes restarted with zero dropped connections"
    ],
    author: "AI-CLAR Automated RCA Engine"
  }
];

export const MOCK_ACTIVITY_CHART = [
  { time: "00:00", requests: 2400, errors: 12 },
  { time: "02:00", requests: 1800, errors: 8 },
  { time: "04:00", requests: 1400, errors: 5 },
  { time: "06:00", requests: 2100, errors: 9 },
  { time: "08:00", requests: 3800, errors: 22 },
  { time: "10:00", requests: 5200, errors: 35 },
  { time: "12:00", requests: 6100, errors: 48 },
  { time: "14:00", requests: 5900, errors: 327 },
  { time: "16:00", requests: 6400, errors: 89 },
  { time: "18:00", requests: 5800, errors: 42 },
  { time: "20:00", requests: 4900, errors: 28 },
  { time: "22:00", requests: 3600, errors: 16 }
];

export const MOCK_ERROR_TREND = [
  { time: "13:00", errors: 14, baseline: 15 },
  { time: "13:20", errors: 18, baseline: 15 },
  { time: "13:40", errors: 19, baseline: 16 },
  { time: "14:00", errors: 45, baseline: 15 },
  { time: "14:10", errors: 140, baseline: 15 },
  { time: "14:20", errors: 327, baseline: 16 },
  { time: "14:30", errors: 185, baseline: 16 },
  { time: "14:40", errors: 88, baseline: 15 },
  { time: "15:00", errors: 34, baseline: 15 }
];
