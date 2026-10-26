import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { Eye, Download, FileText, Clock, Server } from 'lucide-react';

export default function ReportsTable({ reports, onViewReport, onDownloadReport }) {
  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              <th className="py-3 px-6">Incident</th>
              <th className="py-3 px-6">Severity</th>
              <th className="py-3 px-6">Server</th>
              <th className="py-3 px-6">Date</th>
              <th className="py-3 px-6">Status</th>
              <th className="py-3 px-6 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {reports && reports.length > 0 ? (
              reports.map((rep) => (
                <tr key={rep.id} className="hover:bg-slate-50/80 transition-colors">
                  {/* Incident */}
                  <td className="py-4 px-6 font-medium text-slate-900 max-w-sm">
                    <div className="flex items-center gap-2.5">
                      <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                      <div>
                        <span className="font-semibold text-slate-900 block">{rep.title}</span>
                        <span className="text-[11px] text-slate-400 font-normal">
                          Incident ID: {rep.incident_id}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* Severity */}
                  <td className="py-4 px-6">
                    <Badge variant={rep.severity} dot size="sm">
                      {rep.severity}
                    </Badge>
                  </td>

                  {/* Server */}
                  <td className="py-4 px-6">
                    <span className="font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded text-[11px] border border-slate-200">
                      {rep.server}
                    </span>
                  </td>

                  {/* Date */}
                  <td className="py-4 px-6 text-slate-500 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{rep.date}</span>
                    </div>
                  </td>

                  {/* Status */}
                  <td className="py-4 px-6">
                    <Badge variant={rep.status} size="sm">
                      {rep.status}
                    </Badge>
                  </td>

                  {/* Action */}
                  <td className="py-4 px-6 text-right whitespace-nowrap space-x-2">
                    <button
                      onClick={() => onViewReport(rep)}
                      className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 px-2 py-1 rounded transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5 text-slate-400" />
                      <span>View</span>
                    </button>
                    <button
                      onClick={() => onDownloadReport(rep)}
                      className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded transition-colors"
                    >
                      <Download className="w-3.5 h-3.5 text-blue-500" />
                      <span>Download Report</span>
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-400 text-xs">
                  No post-mortem reports available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
