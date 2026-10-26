import React from 'react';
import Card from '../common/Card';
import { CheckCircle2, AlertTriangle, XCircle, Server } from 'lucide-react';

export default function CloudHealthSection({ health }) {
  const healthy = health?.healthy_count ?? 24;
  const warning = health?.warning_count ?? 2;
  const critical = health?.critical_count ?? 1;
  const total = health?.total_servers ?? 27;

  const healthyPct = Math.round((healthy / total) * 100);
  const warningPct = Math.round((warning / total) * 100);
  const criticalPct = Math.round((critical / total) * 100);

  return (
    <Card className="p-3.5 sm:p-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2.5">
        <div>
          <h2 className="text-xs sm:text-sm font-semibold text-slate-900">Cloud Cluster Health Overview</h2>
          <p className="text-[11px] text-slate-500">
            Active telemetry status across {total} provisioned cloud nodes
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Server className="w-3.5 h-3.5 text-slate-400" />
          <span>Region: <strong className="text-slate-800">us-east-1</strong></span>
        </div>
      </div>

      {/* Progress bar showing proportion */}
      <div className="w-full h-1.5 rounded-full bg-slate-100 flex overflow-hidden mb-2.5">
        <div style={{ width: `${healthyPct}%` }} className="bg-emerald-500 h-full" title={`Healthy: ${healthy}`} />
        <div style={{ width: `${warningPct}%` }} className="bg-amber-400 h-full" title={`Warning: ${warning}`} />
        <div style={{ width: `${criticalPct}%` }} className="bg-red-500 h-full" title={`Critical: ${critical}`} />
      </div>

      {/* Server Status Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
        {/* Healthy */}
        <div className="flex items-center gap-2.5 p-2 sm:p-2.5 rounded-md border border-slate-200/80 bg-slate-50/50">
          <div className="p-1.5 rounded-md bg-emerald-50 text-emerald-600 border border-emerald-100 shrink-0">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-baseline gap-1">
              <span className="text-base sm:text-lg font-bold text-slate-900">{healthy}</span>
              <span className="text-[11px] text-slate-500 font-medium">servers</span>
            </div>
            <p className="text-[11px] font-medium text-emerald-700 truncate">Healthy (Normal load)</p>
          </div>
        </div>

        {/* Warning */}
        <div className="flex items-center gap-2.5 p-2 sm:p-2.5 rounded-md border border-slate-200/80 bg-slate-50/50">
          <div className="p-1.5 rounded-md bg-amber-50 text-amber-600 border border-amber-100 shrink-0">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-baseline gap-1">
              <span className="text-base sm:text-lg font-bold text-slate-900">{warning}</span>
              <span className="text-[11px] text-slate-500 font-medium">servers</span>
            </div>
            <p className="text-[11px] font-medium text-amber-700 truncate">Warning (Auth/Elevated)</p>
          </div>
        </div>

        {/* Critical */}
        <div className="flex items-center gap-2.5 p-2 sm:p-2.5 rounded-md border border-slate-200/80 bg-slate-50/50">
          <div className="p-1.5 rounded-md bg-red-50 text-red-600 border border-red-100 shrink-0">
            <XCircle className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-baseline gap-1">
              <span className="text-base sm:text-lg font-bold text-slate-900">{critical}</span>
              <span className="text-[11px] text-slate-500 font-medium">server</span>
            </div>
            <p className="text-[11px] font-medium text-red-700 truncate">Critical (Failure active)</p>
          </div>
        </div>
      </div>
    </Card>
  );
}
