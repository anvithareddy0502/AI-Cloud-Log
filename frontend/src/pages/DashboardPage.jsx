import React, { useState, useEffect } from 'react';
import KpiCard from '../components/dashboard/KpiCard';
import CloudHealthSection from '../components/dashboard/CloudHealthSection';
import ProminentIncidentCard from '../components/dashboard/ProminentIncidentCard';
import ActivityChart from '../components/dashboard/ActivityChart';
import ErrorTrendChart from '../components/dashboard/ErrorTrendChart';
import RecentIncidentsTable from '../components/dashboard/RecentIncidentsTable';
import CriticalAlertsBanner from '../components/dashboard/CriticalAlertsBanner';
import { api } from '../services/api';
import { useApp } from '../context/AppContext';
import { Activity, Flame, AlertTriangle, XCircle, RefreshCw, ScrollText } from 'lucide-react';

export default function DashboardPage() {
  const { setSelectedIncidentId, setActiveTab, showToast } = useApp();
  const [data, setData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadStats = async () => {
    try {
      const [res, alertsRes] = await Promise.all([
        api.getDashboardStats(),
        api.getAlerts(true)
      ]);
      setData(res);
      setAlerts(alertsRes || []);
    } catch (err) {
      console.error("Failed to load dashboard statistics", err);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAlertRead = async (alertId) => {
    try {
      await api.markAlertRead(alertId);
      setAlerts(prev => prev.filter(a => (a.alert_id || a.id) !== alertId));
      showToast('Alert marked as read', 'success');
    } catch (err) {
      console.error("Failed to mark alert read:", err);
      showToast('Failed to mark alert as read', 'error');
    }
  };

  const handleInvestigate = (incidentId) => {
    if (incidentId) {
      setSelectedIncidentId(incidentId);
      setActiveTab('incidents');
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  return (
    <div className="space-y-3.5 sm:space-y-4">
      {/* Top Bar / Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">Cloud Observability Overview</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time telemetry, automated log correlation, and AI-driven root-cause indicators
          </p>
        </div>
        <button
          onClick={loadStats}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-2.5 py-1.5 rounded-md shadow-xs transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Critical Alerts Banner */}
      <CriticalAlertsBanner
        alerts={alerts}
        onMarkRead={handleMarkAlertRead}
        onInvestigate={handleInvestigate}
      />

      {/* TOP: Real KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-3">
        <KpiCard
          title="Cloud Health"
          value={`${data?.kpis?.cloud_health_pct ?? 98.4}%`}
          subtitle="Cluster status"
          status={data?.kpis?.cloud_health_pct < 60 ? "critical" : data?.kpis?.cloud_health_pct < 80 ? "warning" : "healthy"}
          icon={Activity}
        />
        <KpiCard
          title="Total Logs"
          value={`${data?.kpis?.total_logs ?? 64}`}
          subtitle="Events in DB"
          status="info"
          icon={ScrollText}
        />
        <KpiCard
          title="Active Incidents"
          value={`${data?.kpis?.active_incidents ?? 0}`}
          subtitle="Open / Investigating"
          status={data?.kpis?.active_incidents > 0 ? "critical" : "healthy"}
          icon={Flame}
        />
        <KpiCard
          title="Critical Incidents"
          value={`${data?.kpis?.critical_incidents ?? 0}`}
          subtitle="P1 severity"
          status={data?.kpis?.critical_incidents > 0 ? "critical" : "healthy"}
          icon={AlertTriangle}
        />
        <KpiCard
          title="Anomalies"
          value={`${data?.kpis?.anomalies_detected ?? 14}`}
          subtitle="IsolationForest ML"
          status="warning"
          icon={AlertTriangle}
        />
        <KpiCard
          title="Critical Errors"
          value={`${data?.kpis?.critical_errors ?? 28}`}
          subtitle="Urgent log events"
          status="critical"
          icon={XCircle}
        />
      </div>

      {/* SECTION 1: Cloud Health Overview */}
      <section>
        <CloudHealthSection health={data?.server_health} />
      </section>

      {/* SECTION 2: AI Detected Incident */}
      <section>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Prioritized Alert
          </span>
        </div>
        <ProminentIncidentCard incident={data?.prominent_incident} />
      </section>

      {/* SECTION 3: Two Simple Charts */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-3.5">
        <ActivityChart data={data?.activity_chart} />
        <ErrorTrendChart data={data?.error_trend_chart} />
      </section>

      {/* SECTION 4: Recent Incidents Table */}
      <section>
        <RecentIncidentsTable incidents={data?.recent_incidents} />
      </section>
    </div>
  );
}
