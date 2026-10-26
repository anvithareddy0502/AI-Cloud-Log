import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { ShieldCheck, Globe, Clock, Server } from 'lucide-react';

export default function SecurityEventTable({ events }) {
  return (
    <Card className="overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Detected Security Anomalies & Access Audits</h3>
          <p className="text-xs text-slate-500 mt-0.5">Suspicious ingress patterns, failed authentication bursts, and edge policy violations</p>
        </div>
        <span className="text-xs text-slate-500">
          Showing {events?.length || 0} events
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              <th className="py-3 px-6">Risk Level</th>
              <th className="py-3 px-6">Incident & Details</th>
              <th className="py-3 px-6">Server</th>
              <th className="py-3 px-6">Source Location & IP</th>
              <th className="py-3 px-6">Attempts</th>
              <th className="py-3 px-6">Time</th>
              <th className="py-3 px-6">Status / Mitigation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {events && events.map((item) => (
              <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                {/* Risk Level */}
                <td className="py-4 px-6">
                  <Badge variant={item.risk_level === 'High' ? 'critical' : item.risk_level === 'Medium' ? 'warning' : 'healthy'} dot size="sm">
                    {item.risk_level.toUpperCase()} RISK
                  </Badge>
                </td>

                {/* Incident & Details */}
                <td className="py-4 px-6 font-medium text-slate-900 max-w-sm">
                  <div className="flex flex-col">
                    <span className="text-slate-900 font-semibold">{item.title}</span>
                    <span className="text-[11px] text-slate-500 font-normal mt-0.5">
                      {item.details}
                    </span>
                  </div>
                </td>

                {/* Server */}
                <td className="py-4 px-6">
                  <span className="font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded text-[11px] border border-slate-200">
                    {item.server}
                  </span>
                </td>

                {/* Source */}
                <td className="py-4 px-6">
                  <div className="flex flex-col">
                    <div className="flex items-center gap-1 font-mono text-slate-800 text-[11px]">
                      <Globe className="w-3.5 h-3.5 text-slate-400" />
                      <span>{item.source_ip}</span>
                    </div>
                    <span className="text-[11px] text-slate-400 mt-0.5">
                      {item.source_geo}
                    </span>
                  </div>
                </td>

                {/* Attempts */}
                <td className="py-4 px-6">
                  <span className="font-mono font-bold text-slate-800 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
                    {item.attempt_count}
                  </span>
                </td>

                {/* Timestamp */}
                <td className="py-4 px-6 text-slate-500 whitespace-nowrap">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>{item.timestamp}</span>
                  </div>
                </td>

                {/* Status / Mitigation */}
                <td className="py-4 px-6">
                  <div className="flex flex-col gap-1">
                    <Badge variant={item.status} size="sm">
                      {item.status}
                    </Badge>
                    <span className="text-[10px] text-slate-500 truncate max-w-[180px]">
                      {item.action_taken}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
