import React from 'react';
import { AlertTriangle, CheckCircle, ArrowRight, Bell } from 'lucide-react';
import Badge from '../common/Badge';

export default function CriticalAlertsBanner({ alerts = [], onMarkRead, onInvestigate }) {
  const unreadAlerts = alerts.filter(a => !a.read);

  if (unreadAlerts.length === 0) {
    return null;
  }

  return (
    <div className="bg-red-50/70 border border-red-200 rounded-md p-2.5 sm:p-3 shadow-xs transition-all animate-fadeIn">
      <div className="flex items-center justify-between gap-2 mb-2 pb-1.5 border-b border-red-200/60">
        <div className="flex items-center gap-1.5">
          <div className="w-5 h-5 rounded-full bg-red-100 flex items-center justify-center text-red-600 shrink-0">
            <Bell className="w-3 h-3 animate-pulse" />
          </div>
          <span className="text-[11px] font-bold text-red-900 uppercase tracking-wider">
            Critical Telemetry Alerts ({unreadAlerts.length} Active)
          </span>
        </div>
        <Badge variant="Critical" size="sm">
          P1 DISPATCH
        </Badge>
      </div>

      <div className="space-y-1.5">
        {unreadAlerts.slice(0, 2).map((alert) => (
          <div
            key={alert.alert_id || alert.id}
            className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-white border border-red-100 px-3 py-2 rounded shadow-xs"
          >
            <div className="space-y-0.5 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-900 truncate">
                  {alert.title}
                </span>
                <span className="text-[10px] font-mono text-slate-400 shrink-0">
                  {alert.created_at}
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-snug">
                {alert.message}
              </p>
            </div>

            <div className="flex items-center gap-1.5 self-start sm:self-center shrink-0">
              <button
                onClick={() => onMarkRead && onMarkRead(alert.alert_id || alert.id)}
                className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-2 py-1 rounded transition-colors"
                title="Mark this alert as read"
              >
                <CheckCircle className="w-3 h-3 text-emerald-600" />
                <span>Mark Read</span>
              </button>

              <button
                onClick={() => onInvestigate && onInvestigate(alert.incident_id)}
                className="inline-flex items-center gap-1 text-[11px] font-medium text-white bg-red-600 hover:bg-red-700 px-2 py-1 rounded shadow-xs transition-colors"
                title="Open incident analysis for this alert"
              >
                <span>Investigate</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}