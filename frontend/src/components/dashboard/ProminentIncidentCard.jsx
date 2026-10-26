import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import Button from '../common/Button';
import { ArrowRight, Flame, Server, Layers, Clock, AlertOctagon } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function ProminentIncidentCard({ incident }) {
  const { navigateToIncident } = useApp();

  const current = incident || {
    id: 'inc-01',
    title: 'Database Connectivity Failure',
    severity: 'Critical',
    affected_server: 'Server-03',
    affected_service: 'Payment API',
    related_events_count: 327,
    detected_relative: '2 min ago',
    ai_summary: 'The system detected an abnormal increase in database connection failures. API response time also increased and payment requests began failing shortly afterward.'
  };

  return (
    <Card className="p-3 sm:p-3.5 border-l-4 border-l-red-500 bg-white shadow-xs">
      <div className="space-y-2">
        {/* Top Badges & Meta */}
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="critical" dot size="sm">
            CRITICAL INCIDENT
          </Badge>
          <span className="text-[11px] text-slate-400 font-mono">ID: {current.id}</span>
          <span className="text-slate-300">•</span>
          <div className="flex items-center gap-1 text-[11px] text-slate-500">
            <Clock className="w-3 h-3 text-slate-400" />
            <span>Detected {current.detected_relative}</span>
          </div>
        </div>

        {/* Title & Summary */}
        <div>
          <h2 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
            {current.title}
          </h2>
          <p className="text-xs text-slate-600 mt-0.5 leading-snug">
            {current.ai_summary}
          </p>
        </div>

        {/* Telemetry Pills & CTA Button aligned together */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 border-t border-slate-100">
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-600">
            <div className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
              <Server className="w-3 h-3 text-slate-400" />
              <span>Server: <strong className="text-slate-800">{current.affected_server}</strong></span>
            </div>
            <div className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
              <Layers className="w-3 h-3 text-slate-400" />
              <span>Service: <strong className="text-slate-800">{current.affected_service}</strong></span>
            </div>
            <div className="flex items-center gap-1 bg-red-50 px-2 py-0.5 rounded border border-red-200/60 text-red-700 font-medium">
              <AlertOctagon className="w-3 h-3 text-red-500" />
              <span>{current.related_events_count} Events Correlated</span>
            </div>
          </div>

          <Button
            variant="primary"
            size="sm"
            icon={ArrowRight}
            onClick={() => navigateToIncident(current.id)}
            className="self-start sm:self-auto text-xs shrink-0 shadow-xs"
          >
            View AI Analysis
          </Button>
        </div>
      </div>
    </Card>
  );
}
