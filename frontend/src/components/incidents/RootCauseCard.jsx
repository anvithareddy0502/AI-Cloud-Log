import React from 'react';
import Card from '../common/Card';
import { Target, ShieldCheck } from 'lucide-react';

export default function RootCauseCard({ rootCause, confidence }) {
  return (
    <Card className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Likely Root Cause */}
        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <Target className="w-4 h-4 text-blue-600" />
            <span>Likely Root Cause</span>
          </div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">
            {rootCause || 'Database connection exhaustion'}
          </h2>
          <p className="text-xs text-slate-500">
            Identified via multi-server temporal log correlation and causal dependency graphs.
          </p>
        </div>

        {/* Confidence Meter */}
        <div className="sm:border-l sm:border-slate-200 sm:pl-6 text-left sm:text-right min-w-[140px]">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
            Confidence
          </span>
          <div className="flex items-baseline gap-1 sm:justify-end">
            <span className="text-3xl font-extrabold text-blue-600 tracking-tight">
              {confidence || 91}%
            </span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-blue-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${confidence || 91}%` }}
            />
          </div>
        </div>
      </div>
    </Card>
  );
}
