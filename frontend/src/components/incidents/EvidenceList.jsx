import React from 'react';
import Card from '../common/Card';
import { CheckCircle2, Activity } from 'lucide-react';

export default function EvidenceList({ evidence }) {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
          Evidence
        </h3>
        <span className="text-xs text-slate-400 font-medium">
          {evidence?.length || 0} correlated telemetry indicators
        </span>
      </div>

      <div className="space-y-3">
        {evidence && evidence.map((item, idx) => (
          <div
            key={idx}
            className="flex items-start gap-3 p-3 rounded-lg border border-slate-200/80 bg-slate-50/60"
          >
            <div className="mt-0.5 text-blue-600">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <p className="text-xs font-medium text-slate-800 leading-normal">
              {item}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}
