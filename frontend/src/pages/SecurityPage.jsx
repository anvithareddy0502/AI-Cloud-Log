import React, { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import SecurityEventTable from '../components/security/SecurityEventTable';
import { api } from '../services/api';
import { ShieldCheck, ShieldAlert, Lock, AlertTriangle, Globe, RefreshCw } from 'lucide-react';

export default function SecurityPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadSecurityData = async () => {
    setRefreshing(true);
    try {
      const data = await api.getSecurityEvents();
      setEvents(data || []);
    } catch (err) {
      console.error("Failed to load security audit events:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadSecurityData();
  }, []);

  // Compute dynamic security metrics from real database records
  const flaggedIps = Array.from(new Set(events.map(e => e.source_ip || e.ip).filter(Boolean)));
  const totalFailedLogins = events
    .filter(e => (e.event_type || "").toLowerCase().includes("login") || (e.event_type || "").toLowerCase().includes("auth"))
    .reduce((acc, e) => acc + (e.attempt_count || 1), 0);
  
  const highRiskEvents = events.filter(e => 
    (e.risk_level || "").toUpperCase() === "HIGH" || (e.risk_level || "").toUpperCase() === "CRITICAL"
  );

  const prominentEvent = highRiskEvents[0] || events[0] || null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Cloud Security & Access Audit
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Ingress attack vectors, anomalous credential bursts, and perimeter authorization integrity
          </p>
        </div>

        <button
          onClick={loadSecurityData}
          disabled={refreshing}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-3 py-1.5 rounded-md shadow-xs transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Audit</span>
        </button>
      </div>

      {/* Security Posture Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium">Security Posture</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <span className="text-xl font-bold text-slate-900">
            {highRiskEvents.length > 0 ? "Under Threat" : "Protected"}
          </span>
          <p className="text-[11px] text-emerald-700 font-medium mt-1">
            {highRiskEvents.length} high-risk anomaly detected
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium">Flagged IP Addresses</span>
            <Globe className="w-4 h-4 text-amber-600" />
          </div>
          <span className="text-xl font-bold text-slate-900">
            {flaggedIps.length} Throttled
          </span>
          <p className="text-[11px] text-slate-500 mt-1 font-mono">
            {flaggedIps[0] ? flaggedIps[0] : "None"}
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium">Failed Logins</span>
            <Lock className="w-4 h-4 text-red-600" />
          </div>
          <span className="text-xl font-bold text-slate-900">
            {totalFailedLogins} Blocked
          </span>
          <p className="text-[11px] text-slate-500 mt-1">
            Captured across {events.length} security audits
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium">Active Threat Incidents</span>
            <ShieldAlert className="w-4 h-4 text-blue-600" />
          </div>
          <span className="text-xl font-bold text-slate-900">
            {events.filter(e => e.status === "ACTIVE").length} Active
          </span>
          <p className="text-[11px] text-slate-500 mt-1">Real-time edge telemetry</p>
        </Card>
      </div>

      {/* Prominent High-Risk Card */}
      {prominentEvent ? (
        <Card className="p-6 border-l-4 border-l-amber-500 bg-white">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant={prominentEvent.risk_level === 'CRITICAL' ? 'critical' : 'warning'} dot size="sm">
                  {prominentEvent.risk_level || 'HIGH RISK'} ANOMALY
                </Badge>
                <span className="text-xs font-mono text-slate-400">{prominentEvent.server}</span>
              </div>
              <h2 className="text-base font-bold text-slate-900">
                {prominentEvent.event_type}
              </h2>
              <p className="text-xs text-slate-600">
                <strong className="text-slate-800">{prominentEvent.attempt_count} attempt(s) detected</strong>: {prominentEvent.evidence}
              </p>
            </div>
            <div className="text-left sm:text-right">
              <Badge variant="healthy" size="sm">
                Status: {prominentEvent.status || 'Active'}
              </Badge>
              <p className="text-[11px] text-slate-400 mt-1.5 font-mono">
                Source: {prominentEvent.source_ip}
              </p>
            </div>
          </div>
        </Card>
      ) : null}

      {/* Security Audit Table */}
      <SecurityEventTable events={events} />
    </div>
  );
}
