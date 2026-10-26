import {
  MOCK_SERVERS,
  MOCK_INCIDENTS,
  MOCK_ANOMALIES,
  MOCK_SECURITY_EVENTS,
  MOCK_LOGS_LIST,
  MOCK_REPORTS,
  MOCK_ACTIVITY_CHART,
  MOCK_ERROR_TREND,
} from './mockData';

const BASE_URL = '/api';

async function safeFetch(url, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    console.info(`[AI-CLAR API Client] Fetch to '${url}' fallback triggered (${err.message}). Using local mock repository.`);
    return null;
  }
}

export const api = {
  // Upload logs
  async uploadLogs(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${BASE_URL}/logs/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Upload failed with HTTP ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error('[AI-CLAR API Client] Upload error:', err.message);
      throw err;
    }
  },

  // Dynamic Telemetry Document Counts (Sidebar Badges)
  async getSystemCounts() {
    const data = await safeFetch('/system/counts');
    if (data && data.status === 'success') return data;
    const stats = await safeFetch('/dashboard/stats');
    if (stats?.kpis) {
      return {
        anomalies: stats.kpis.anomalies_detected ?? 0,
        total_anomalies: stats.kpis.anomalies_detected ?? 0,
        incidents: stats.kpis.active_incidents ?? stats.kpis.total_incidents ?? 0,
        total_incidents: stats.kpis.total_incidents ?? stats.kpis.active_incidents ?? 0,
        active_incidents: stats.kpis.active_incidents ?? 0,
      };
    }
    return null;
  },

  // Dashboard Stats
  async getDashboardStats() {
    const data = await safeFetch('/dashboard/stats');
    if (data) return data;

    const healthy = MOCK_SERVERS.filter(s => s.status === 'healthy').length + 21;
    const warning = MOCK_SERVERS.filter(s => s.status === 'warning').length;
    const critical = MOCK_SERVERS.filter(s => s.status === 'critical').length;
    const total = healthy + warning + critical;

    return {
      kpis: {
        cloud_health_pct: 98.4,
        active_incidents: 3,
        anomalies_detected: 14,
        critical_errors: 28,
      },
      server_health: {
        total_servers: total,
        healthy_count: healthy,
        warning_count: warning,
        critical_count: critical,
        health_percentage: 98.4,
      },
      prominent_incident: MOCK_INCIDENTS[0],
      activity_chart: MOCK_ACTIVITY_CHART,
      error_trend_chart: MOCK_ERROR_TREND,
      recent_incidents: MOCK_INCIDENTS,
    };
  },

  // Logs
  async getLogs(filters = {}) {
    const params = new URLSearchParams();
    if (filters.server && filters.server !== 'All') params.append('server', filters.server);
    if (filters.service && filters.service !== 'All') params.append('service', filters.service);
    if (filters.severity && filters.severity !== 'All') params.append('severity', filters.severity);
    if (filters.search) params.append('search', filters.search);
    if (filters.time_range) params.append('time_range', filters.time_range);
    if (filters.limit) params.append('limit', filters.limit);

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const data = await safeFetch(`/logs${queryString}`);
    if (data) return data;

    // Filter mock logs
    let filtered = [...MOCK_LOGS_LIST];
    if (filters.server && filters.server !== 'All') {
      filtered = filtered.filter(l => l.server.toLowerCase() === filters.server.toLowerCase());
    }
    if (filters.service && filters.service !== 'All') {
      filtered = filtered.filter(l => l.service.toLowerCase() === filters.service.toLowerCase());
    }
    if (filters.severity && filters.severity !== 'All') {
      filtered = filtered.filter(l => l.severity.toLowerCase() === filters.severity.toLowerCase());
    }
    if (filters.search) {
      const q = filters.search.toLowerCase();
      filtered = filtered.filter(
        l => l.message.toLowerCase().includes(q) ||
             l.server.toLowerCase().includes(q) ||
             (l.correlation_id && l.correlation_id.toLowerCase().includes(q))
      );
    }

    return {
      total: filtered.length,
      count: filtered.length,
      logs: filtered,
    };
  },

  async getLogById(id) {
    const data = await safeFetch(`/logs/${id}`);
    if (data) return data;
    return MOCK_LOGS_LIST.find(l => l.id === id) || null;
  },

  // Incidents
  async getIncidents(filters = {}) {
    const params = new URLSearchParams();
    if (filters.severity && filters.severity !== 'All') params.append('severity', filters.severity);
    if (filters.status && filters.status !== 'All') params.append('status', filters.status);
    if (filters.server && filters.server !== 'All') params.append('server', filters.server);
    if (filters.service && filters.service !== 'All') params.append('service', filters.service);
    if (filters.start_time) params.append('start_time', filters.start_time);
    if (filters.end_time) params.append('end_time', filters.end_time);

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const data = await safeFetch(`/incidents${queryString}`);
    if (data) return data;
    return MOCK_INCIDENTS;
  },

  async getIncidentById(id) {
    if (!id) return null;
    const data = await safeFetch(`/incidents/${id}`);
    if (data) return data;
    return MOCK_INCIDENTS.find(i => i.id === id) || MOCK_INCIDENTS[0];
  },

  async resolveIncident(id) {
    const data = await safeFetch(`/incidents/${id}/resolve`, {
      method: 'POST',
    });
    if (data) return data;
    const item = MOCK_INCIDENTS.find(i => i.id === id);
    if (item) item.status = 'RESOLVED';
    return { message: 'Incident marked as Resolved', incident: item };
  },

  async ignoreIncident(id) {
    const data = await safeFetch(`/incidents/${id}/ignore`, {
      method: 'POST',
    });
    if (data) return data;
    const item = MOCK_INCIDENTS.find(i => i.id === id);
    if (item) item.status = 'IGNORED';
    return { message: 'Incident marked as Ignored', incident: item };
  },

  async updateIncidentStatus(id, status) {
    const data = await safeFetch(`/incidents/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({ status }),
    });
    if (data) return data;
    const item = MOCK_INCIDENTS.find(i => i.id === id);
    if (item) item.status = status;
    return { message: 'Status updated', incident: item };
  },

  // Anomalies
  async getAnomalies() {
    const data = await safeFetch('/anomalies');
    if (data) return data;
    return MOCK_ANOMALIES;
  },

  // Security Events
  async getSecurityEvents(filters = {}) {
    const params = new URLSearchParams();
    if (filters.risk_level && filters.risk_level !== 'All') params.append('risk_level', filters.risk_level);
    if (filters.server && filters.server !== 'All') params.append('server', filters.server);
    if (filters.event_type && filters.event_type !== 'All') params.append('event_type', filters.event_type);
    if (filters.status && filters.status !== 'All') params.append('status', filters.status);

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const data = await safeFetch(`/security-events${queryString}`);
    if (data) return data;
    return MOCK_SECURITY_EVENTS;
  },

  // AI Incident Explanation
  async getIncidentAiExplanation(incidentId) {
    if (!incidentId) return null;
    return await safeFetch(`/incidents/${incidentId}/ai-explanation`);
  },

  // Servers
  async getServers() {
    const data = await safeFetch('/servers');
    if (data) return data;
    return MOCK_SERVERS;
  },

  // Reports
  async getReports() {
    const data = await safeFetch('/reports');
    if (data) return data;
    return MOCK_REPORTS;
  },

  async generateReport(incidentId) {
    const data = await safeFetch('/reports/generate', {
      method: 'POST',
      body: JSON.stringify({ incident_id: incidentId }),
    });
    if (data) return data;

    const inc = MOCK_INCIDENTS.find(i => i.id === incidentId) || MOCK_INCIDENTS[0];
    const newRep = {
      id: `rep-${Date.now().toString().slice(-4)}`,
      incident_id: inc.id,
      title: `Executive Post-Mortem: ${inc.title}`,
      severity: inc.severity,
      server: inc.affected_server,
      service: inc.affected_service,
      date: new Date().toISOString().replace('T', ' ').slice(0, 19),
      status: 'Generated',
      summary: inc.ai_summary,
      likely_root_cause: inc.likely_root_cause,
      impact_scope: `${inc.affected_service} on ${inc.affected_server}`,
      mitigation_steps: inc.recommended_actions,
      author: 'AI-CLAR Automated RCA Engine',
    };
    MOCK_REPORTS.unshift(newRep);
    return newRep;
  },

  // Alerts System
  async getAlerts(unreadOnly = false) {
    const data = await safeFetch(`/alerts?unread_only=${unreadOnly}`);
    if (data && data.alerts) return data.alerts;
    return [
      {
        alert_id: "alt-01",
        incident_id: "inc-01",
        title: "Database Connection Pool Exhaustion Alert",
        severity: "CRITICAL",
        message: "Critical incident detected on Server-03: Database Connection Pool Exhaustion affecting PostgreSQL Database.",
        created_at: "2 min ago",
        read: false
      }
    ];
  },

  async markAlertRead(alertId) {
    return await safeFetch(`/alerts/${alertId}/read`, {
      method: 'POST',
    });
  },

  async markAllAlertsRead() {
    return await safeFetch('/alerts/mark-all-read', {
      method: 'POST',
    });
  },

  // AWS CloudWatch Integration
  async getCloudWatchStatus() {
    const data = await safeFetch('/cloudwatch/status');
    if (data) return data;
    return {
      status: "not_configured",
      is_configured: false,
      region: "us-east-1",
      log_group: "/aws/cloud/logs",
      streams_available: 0,
      message: "AWS credentials not configured. Local uploads fully operational."
    };
  },

  async getCloudWatchStreams(logGroup) {
    const query = logGroup ? `?log_group=${encodeURIComponent(logGroup)}` : '';
    const data = await safeFetch(`/cloudwatch/streams${query}`);
    return data ? data.streams : [];
  },

  async getCloudWatchLogs(logGroup, streamName, limit = 50) {
    const params = new URLSearchParams();
    if (logGroup) params.append('log_group', logGroup);
    if (streamName) params.append('stream_name', streamName);
    params.append('limit', limit);
    const data = await safeFetch(`/cloudwatch/logs?${params.toString()}`);
    return data ? data.logs : [];
  },

  async ingestCloudWatchLogs(logGroup, limit = 50) {
    const params = new URLSearchParams();
    if (logGroup) params.append('log_group', logGroup);
    params.append('limit', limit);
    return await safeFetch(`/cloudwatch/ingest?${params.toString()}`, {
      method: 'POST',
    });
  },

  // PDF Incident Report
  getIncidentReportUrl(incidentId) {
    return `${BASE_URL}/incidents/${incidentId}/report`;
  },

  downloadIncidentReport(incidentId) {
    const downloadUrl = `${BASE_URL}/incidents/${incidentId}/report`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', `AI-CLAR-Report-${incidentId}.pdf`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  // System & Health Status
  async getSystemStatus() {
    const data = await safeFetch('/system/status');
    if (data) return data;
    return {
      status: "healthy",
      database: { mode: "Resilient In-Memory", connected: false },
      ml_engine: { model: "IsolationForest", is_fitted: true, contamination: 0.15 },
      cloudwatch: { is_configured: false }
    };
  },

  // AI Assistant
  async askAi(question) {
    const data = await safeFetch('/ai/ask', {
      method: 'POST',
      body: JSON.stringify({ question }),
    });
    if (data) return data;
    return this.sendAssistantQuery(question);
  },

  async sendAssistantQuery(query, context = {}) {
    const data = await safeFetch('/ai/ask', {
      method: 'POST',
      body: JSON.stringify({
        question: query,
        query: query,
        context_server: context.server || null,
        context_incident: context.incident || null,
      }),
    });
    if (data) return data;

    // Fallback dynamic query match
    const q = query.toLowerCase();
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (q.includes('critical') || q.includes('error')) {
      return {
        message_id: `msg-${Date.now()}`,
        answer: "There is currently 1 active CRITICAL incident:\n\n**Database Connectivity Failure** on **Server-03** affecting the **Payment API**.\n- Detected 2 minutes ago with **327 correlated timeout logs**.\n- Likely Root Cause: **Database connection exhaustion** (Confidence: 91%).\n- Recommended immediate action: Check active connections and increase connection pool limits.",
        timestamp: timeStr,
        related_server: "Server-03",
        related_incident_id: "inc-01",
        confidence_score: 91,
        key_evidence: [
          "327 timeout events in 4 minutes",
          "Error rate +420%",
          "Active connections reached 99.4% ceiling"
        ],
        suggested_followups: [
          "Why did Server-03 fail?",
          "What caused the latest incident?",
          "Show recommended mitigation steps for Server-03"
        ]
      };
    } else if (q.includes('server-03') || q.includes('server 03') || q.includes('server 3') || q.includes('fail')) {
      return {
        message_id: `msg-${Date.now()}`,
        answer: "Analysis for **Server-03** (10.0.2.45, us-east-1c):\n\n- **Current Status**: Critical\n- **CPU**: 96.8% | **Memory**: 91.2%\n- **Failure Mechanism**: The PostgreSQL connection pool (HikariCP) reached maximum capacity (500/500 sockets), rejecting incoming requests from the Payment API.\n- **Related Logs**: 327 timeout events logged under correlation ID `corr-db-9842`.",
        timestamp: timeStr,
        related_server: "Server-03",
        related_incident_id: "inc-01",
        confidence_score: 94,
        key_evidence: [
          "psql: fatal: remaining connection slots reserved",
          "HikariCP-1 failed to deliver connection in 30000ms"
        ],
        suggested_followups: [
          "What are today's critical errors?",
          "Generate incident report for Server-03",
          "Are there any security threats?"
        ]
      };
    } else if (q.includes('security') || q.includes('threat') || q.includes('attack')) {
      return {
        message_id: `msg-${Date.now()}`,
        answer: "Security Status Overview:\n\n- **1 High Risk Alert**: Suspicious Login Activity detected on **Server-02** (Authentication service).\n- **Source IP**: 198.51.100.42 (Frankfurt, Germany).\n- **Attempt Count**: 47 failed authentication attempts targeting root and administrative accounts.\n- **Action Status**: Edge firewall rate-limiting applied. Zero compromised sessions detected.",
        timestamp: timeStr,
        related_server: "Server-02",
        related_incident_id: "inc-02",
        confidence_score: 88,
        key_evidence: [
          "47 failed SSH and PAM attempts within 180s",
          "Attack vector: Automated dictionary brute force"
        ],
        suggested_followups: [
          "Which server has the most problems?",
          "Show full details for Server-02",
          "View security event audit log"
        ]
      };
    } else if (q.includes('problem') || q.includes('which server') || q.includes('most')) {
      return {
        message_id: `msg-${Date.now()}`,
        answer: "Server Problem Assessment:\n\n1. **Server-03 (Most problematic)**: Classified as **Critical**. Responsible for the active database pool failure and 327 errors.\n2. **Server-02**: Classified as **Warning** due to 47 brute-force authentication attempts.\n3. **Server-06**: Classified as **Warning** due to high ingress network buffer saturation (78%).\n\nThe remaining 24 cloud nodes are operating normally with average CPU below 40%.",
        timestamp: timeStr,
        related_server: "Server-03",
        related_incident_id: "inc-01",
        confidence_score: 96,
        key_evidence: [
          "Server-03 CPU at 96.8%, DB Pool at 100%",
          "Server-02 auth anomaly flagged",
          "24 servers healthy"
        ],
        suggested_followups: [
          "Why did Server-03 fail?",
          "What are today's critical errors?",
          "Are there any security threats?"
        ]
      };
    } else {
      return {
        message_id: `msg-${Date.now()}`,
        answer: "The latest incident is **Database Connectivity Failure** (Incident ID: `inc-01`), detected 2 minutes ago on **Server-03**.\n\n- **Trigger**: Abnormal database timeout surge.\n- **Root Cause**: Database connection exhaustion.\n- **Confidence**: 91%\n- **Status**: Currently Investigating by DevOps team.",
        timestamp: timeStr,
        related_server: "Server-03",
        related_incident_id: "inc-01",
        confidence_score: 91,
        key_evidence: [
          "Spike from 4 to 89 errors/min",
          "Cascade to Payment API 504 responses"
        ],
        suggested_followups: [
          "Why did Server-03 fail?",
          "Which server has the most problems?",
          "Generate incident report"
        ]
      };
    }
  },

  // Machine Learning Pipeline & Model Demonstrator
  async getMlModelInfo(dataset = null) {
    const url = dataset ? `/ml/model-info?dataset=${encodeURIComponent(dataset)}` : '/ml/model-info';
    const res = await safeFetch(url);
    if (res && res.model_info) return res;
    return {
      status: 'success',
      model_info: {
        algorithm: 'Isolation Forest',
        model_version: '2.1.0',
        dataset_name: dataset || 'OpenStack',
        training_status: 'Trained',
        is_supervised: false,
        contamination_value: 0.15,
        random_state: 42,
        number_of_features: 16,
        feature_names: [
          'total_events', 'error_count', 'warning_count', 'info_count', 'critical_count',
          'error_rate', 'warning_rate', 'events_per_minute', 'unique_event_ids', 'unique_components',
          'template_entropy', 'avg_response_time', 'max_response_time', 'http_4xx_count',
          'http_5xx_count', 'failed_login_count'
        ],
        number_of_training_samples: 159,
        number_of_testing_samples: 40,
        trained_at: '2026-09-21 21:58:00 UTC',
        evaluation_summary: {
          test_samples_count: 40,
          predicted_anomalies_count: 8,
          anomaly_percentage: 20.0,
          anomaly_score_summary: { min: 0.33, mean: 0.426, max: 0.584, std: 0.069 },
          evaluation_type: 'Unsupervised Outlier Profiling (No ground-truth labels required)'
        }
      },
      academic_notes: 'Unsupervised Isolation Forest trained on 80% numerical telemetry split with zero artificial target labels.'
    };
  },

  async getMlTrainingData(limit = 20, offset = 0, dataset = null) {
    const q = dataset ? `&dataset=${encodeURIComponent(dataset)}` : '';
    const res = await safeFetch(`/ml/training-data?limit=${limit}&offset=${offset}${q}`);
    if (res && res.samples) return res;
    return {
      status: 'success',
      dataset: dataset ? `training_data_${dataset.toLowerCase()}.csv` : 'training_data.csv',
      total_samples: 159,
      offset,
      limit,
      feature_count: 16,
      samples: []
    };
  },

  async getMlTestingData(limit = 20, offset = 0, dataset = null) {
    const q = dataset ? `&dataset=${encodeURIComponent(dataset)}` : '';
    const res = await safeFetch(`/ml/testing-data?limit=${limit}&offset=${offset}${q}`);
    if (res && res.samples) return res;
    return {
      status: 'success',
      dataset: dataset ? `testing_data_${dataset.toLowerCase()}.csv` : 'testing_data.csv',
      total_samples: 40,
      offset,
      limit,
      feature_count: 16,
      samples: []
    };
  },

  async getMlEvaluation(dataset = 'BGL', includeBaselines = false) {
    const res = await safeFetch(`/ml/evaluation?dataset=${encodeURIComponent(dataset)}&include_baselines=${includeBaselines}`);
    return res;
  },

  async retrainMlModel(payload = { dataset: 'OpenStack', contamination: 0.15, random_state: 42 }) {
    try {
      const res = await fetch(`${BASE_URL}/ml/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Retraining failed with HTTP ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error('[AI-CLAR API Client] ML retrain error:', err.message);
      throw err;
    }
  }
};
