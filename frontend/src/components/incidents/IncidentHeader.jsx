import React from 'react';
import Badge from '../common/Badge';
import Button from '../common/Button';
import { Server, Layers, Clock, FileText, CheckCircle, EyeOff } from 'lucide-react';

export default function IncidentHeader({ incident, onGenerateReport, onStatusChange, onResolve, onIgnore }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left main info */}
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={incident.severity} dot size="md">
              {incident.severity}
            </Badge>
            <span className="text-xs font-mono text-slate-400">ID: {incident.id || incident.incident_id}</span>
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Detected {incident.detected_relative || 'recently'} ({incident.detected_at || incident.start_time})</span>
            </div>
            <Badge variant={incident.status} size="md">
              {incident.status}
            </Badge>
          </div>

          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            {incident.title}
          </h1>

          {/* Metadata chips */}
          <div className="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-600">
            <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1 rounded-md">
              <Server className="w-3.5 h-3.5 text-slate-400" />
              <span>Affected Server: <strong className="text-slate-800 font-mono">{incident.affected_server}</strong></span>
            </div>
            <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1 rounded-md">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>Affected Service: <strong className="text-slate-800">{incident.affected_service}</strong></span>
            </div>
          </div>
        </div>

        {/* Right action buttons: Resolve, Ignore, Status, Report */}
        <div className="flex flex-wrap items-center gap-2 self-start lg:self-center">
          <Button
            variant={incident.status === 'RESOLVED' ? 'outline' : 'secondary'}
            size="sm"
            icon={CheckCircle}
            onClick={onResolve}
            className={`text-xs ${incident.status === 'RESOLVED' ? 'text-emerald-700 bg-emerald-50 border-emerald-300' : 'hover:border-emerald-300 hover:text-emerald-700'}`}
          >
            {incident.status === 'RESOLVED' ? 'Resolved' : 'Resolve'}
          </Button>

          <Button
            variant={incident.status === 'IGNORED' ? 'outline' : 'secondary'}
            size="sm"
            icon={EyeOff}
            onClick={onIgnore}
            className={`text-xs ${incident.status === 'IGNORED' ? 'text-slate-500 bg-slate-100 border-slate-300' : 'hover:border-slate-300 hover:text-slate-700'}`}
          >
            {incident.status === 'IGNORED' ? 'Ignored' : 'Ignore'}
          </Button>

          <select
            value={incident.status}
            onChange={(e) => onStatusChange(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 text-slate-700 font-medium cursor-pointer focus:outline-none focus:border-blue-500"
          >
            <option value="OPEN">OPEN</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="IGNORED">IGNORED</option>
          </select>

          <Button
            variant="primary"
            size="sm"
            icon={FileText}
            onClick={onGenerateReport}
            className="whitespace-nowrap text-xs"
          >
            Generate Report
          </Button>
        </div>
      </div>
    </div>
  );
}
