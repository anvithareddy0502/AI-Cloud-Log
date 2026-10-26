import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';

export default function LogTable({ logs, onSelectLog }) {
  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              <th className="py-3 px-5 w-48">Timestamp</th>
              <th className="py-3 px-5 w-28">Server</th>
              <th className="py-3 px-5 w-36">Service</th>
              <th className="py-3 px-5 w-28">Severity</th>
              <th className="py-3 px-5">Message</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs font-mono">
            {logs && logs.length > 0 ? (
              logs.map((log) => (
                <tr
                  key={log.id}
                  onClick={() => onSelectLog(log)}
                  className="hover:bg-blue-50/40 transition-colors cursor-pointer group"
                >
                  {/* Timestamp */}
                  <td className="py-3 px-5 text-slate-500 whitespace-nowrap text-[11px]">
                    {log.timestamp}
                  </td>

                  {/* Server */}
                  <td className="py-3 px-5 whitespace-nowrap font-medium text-slate-700">
                    <span className="bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 text-[11px]">
                      {log.server}
                    </span>
                  </td>

                  {/* Service */}
                  <td className="py-3 px-5 font-sans font-medium text-slate-800 whitespace-nowrap">
                    {log.service}
                  </td>

                  {/* Severity */}
                  <td className="py-3 px-5 whitespace-nowrap font-sans">
                    <Badge variant={log.severity} dot size="sm">
                      {log.severity}
                    </Badge>
                  </td>

                  {/* Message */}
                  <td className="py-3 px-5 text-slate-700 max-w-lg truncate group-hover:text-blue-900">
                    <span className="truncate block font-normal">{log.message}</span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-400 font-sans text-xs">
                  No cloud logs matched the selected filter criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
