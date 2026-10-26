import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import Button from '../common/Button';
import { Clock, Server, Layers, TrendingUp, Sparkles, ArrowRight } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function AnomalyCard({ anomaly }) {
  const { navigateToIncident } = useApp();

  return (
    <Card className="p-5 border border-slate-200 hover:border-slate-300 transition-all">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left main info */}
        <div className="space-y-2 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={anomaly.severity} dot size="sm">
              {anomaly.severity}
            </Badge>
            <span className="text-xs font-mono text-slate-400">ID: {anomaly.id}</span>
            <div className="flex items-center gap-1 text-xs text-slate-400">
              <Clock className="w-3.5 h-3.5" />
              <span>{anomaly.detection_time}</span>
            </div>
            <Badge variant={anomaly.status} size="sm">
              {anomaly.status}
            </Badge>
          </div>

          <div className="flex items-baseline gap-2">
            <h3 className="text-base font-semibold text-slate-900 tracking-tight">
              {anomaly.title}
            </h3>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span className="font-semibold text-slate-700">Reason:</span>
            <span className="bg-slate-100 text-slate-800 px-2 py-0.5 rounded font-mono text-xs">
              {anomaly.reason}
            </span>
          </div>

          {/* Micro telemetry stats */}
          <div className="flex flex-wrap items-center gap-4 pt-1 text-xs text-slate-500">
            <div className="flex items-center gap-1">
              <Server className="w-3.5 h-3.5 text-slate-400" />
              <span>Server: <strong className="text-slate-800 font-mono">{anomaly.server}</strong></span>
            </div>
            <div className="flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>Service: <strong className="text-slate-800">{anomaly.service}</strong></span>
            </div>
            {anomaly.baseline_value && (
              <div className="flex items-center gap-1">
                <TrendingUp className="w-3.5 h-3.5 text-slate-400" />
                <span>Baseline: {anomaly.baseline_value} &rarr; Observed: <strong className="text-red-600">{anomaly.observed_value}</strong></span>
              </div>
            )}
          </div>
        </div>

        {/* Right Confidence & Action */}
        <div className="flex items-center md:flex-col md:items-end justify-between gap-3 pt-3 md:pt-0 border-t md:border-t-0 border-slate-100">
          <div className="text-right">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
              Confidence
            </span>
            <div className="flex items-center gap-1 font-bold text-blue-600 text-lg">
              <Sparkles className="w-4 h-4 text-blue-500" />
              <span>{anomaly.confidence}%</span>
            </div>
          </div>

          <Button
            variant="secondary"
            size="sm"
            icon={ArrowRight}
            onClick={() => navigateToIncident('inc-01')}
            className="hover:border-blue-300 hover:text-blue-700"
          >
            Investigate
          </Button>
        </div>
      </div>
    </Card>
  );
}
