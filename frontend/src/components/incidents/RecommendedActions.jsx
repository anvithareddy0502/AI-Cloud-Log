import React, { useState } from 'react';
import Card from '../common/Card';
import { CheckSquare, Square, Wrench } from 'lucide-react';

export default function RecommendedActions({ actions }) {
  const [completed, setCompleted] = useState({});

  const toggleAction = (idx) => {
    setCompleted(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const defaultActions = [
    "Check database availability and active replication lag",
    "Check active connections using 'SELECT count(*) FROM pg_stat_activity'",
    "Check connection pool limits and max_connections parameters in pgbouncer/db config",
    "Review recent database changes or unindexed migration scripts deployed to Server-03"
  ];

  const list = actions && actions.length > 0 ? actions : defaultActions;

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Wrench className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
            Recommended Actions
          </h3>
        </div>
        <span className="text-xs text-slate-400 font-medium">
          Step-by-step remediation runbook
        </span>
      </div>

      <div className="space-y-2.5">
        {list.map((act, idx) => {
          const isDone = !!completed[idx];
          return (
            <div
              key={idx}
              onClick={() => toggleAction(idx)}
              className={`flex items-start gap-3.5 p-3 rounded-lg border transition-colors cursor-pointer select-none ${
                isDone
                  ? 'bg-slate-50 border-slate-200 text-slate-400 line-through'
                  : 'bg-white border-slate-200 hover:border-blue-200 hover:bg-blue-50/20 text-slate-800'
              }`}
            >
              <span className={`flex items-center justify-center w-5 h-5 rounded text-xs font-bold shrink-0 ${
                isDone ? 'bg-slate-200 text-slate-500' : 'bg-blue-100 text-blue-700'
              }`}>
                {idx + 1}
              </span>
              <p className="text-xs font-medium leading-relaxed flex-1">
                {act}
              </p>
              {isDone ? (
                <CheckSquare className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
              ) : (
                <Square className="w-4 h-4 text-slate-300 shrink-0 mt-0.5" />
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
