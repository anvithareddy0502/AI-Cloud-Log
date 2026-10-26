import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import Button from '../common/Button';
import { ArrowUpRight, Clock, Server } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function RecentIncidentsTable({ incidents }) {
  const { navigateToIncident } = useApp();

  return (
    <Card className="overflow-hidden">
      <div className="px-3.5 py-2.5 border-b border-slate-200/90 flex items-center justify-between">
        <div>
          <h3 className="text-xs sm:text-sm font-semibold text-slate-900">Recent Correlated Incidents</h3>
          <p className="text-[11px] text-slate-500">Multi-server clustered cloud incidents</p>
        </div>
        <span className="text-[11px] text-slate-400 font-medium">
          Showing {incidents?.length || 0} active & recent
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/75 border-b border-slate-200/80 text-[10px] sm:text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              <th className="py-2 px-3">Severity</th>
              <th className="py-2 px-3">Incident</th>
              <th className="py-2 px-3">Server</th>
              <th className="py-2 px-3">Service</th>
              <th className="py-2 px-3">Detected</th>
              <th className="py-2 px-3">Status</th>
              <th className="py-2 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {incidents && incidents.map((item) => (
              <tr
                key={item.id}
                className="hover:bg-slate-50/80 transition-colors group cursor-pointer"
                onClick={() => navigateToIncident(item.id)}
              >
                {/* Severity */}
                <td className="py-2 px-3 whitespace-nowrap">
                  <Badge variant={item.severity} dot size="sm">
                    {item.severity}
                  </Badge>
                </td>

                {/* Incident Title */}
                <td className="py-2 px-3 font-medium text-slate-900">
                  <div className="flex flex-col">
                    <span className="truncate max-w-xs">{item.title}</span>
                    <span className="text-[11px] text-slate-400 font-normal truncate max-w-xs">
                      {item.likely_root_cause}
                    </span>
                  </div>
                </td>

                {/* Server */}
                <td className="py-2 px-3 whitespace-nowrap">
                  <span className="font-mono text-slate-700 bg-slate-100/80 px-1.5 py-0.5 rounded text-[11px] border border-slate-200">
                    {item.affected_server}
                  </span>
                </td>

                {/* Service */}
                <td className="py-2 px-3 text-slate-600 font-medium whitespace-nowrap">
                  {item.affected_service}
                </td>

                {/* Detected */}
                <td className="py-2 px-3 text-slate-500 whitespace-nowrap">
                  <div className="flex items-center gap-1 text-[11px]">
                    <Clock className="w-3 h-3 text-slate-400 shrink-0" />
                    <span>{item.detected_relative}</span>
                  </div>
                </td>

                {/* Status */}
                <td className="py-2 px-3 whitespace-nowrap">
                  <Badge variant={item.status} size="sm">
                    {item.status}
                  </Badge>
                </td>

                {/* Action */}
                <td className="py-2 px-3 text-right whitespace-nowrap">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigateToIncident(item.id);
                    }}
                    className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800"
                  >
                    <span>Analyze</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
