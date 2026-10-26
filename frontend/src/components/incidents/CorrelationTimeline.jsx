import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { GitCommit, Clock, Server, Layers } from 'lucide-react';

export default function CorrelationTimeline({ timeline }) {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
            Correlated Incident Timeline
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Temporal log correlation establishing chronological root cause
          </p>
        </div>
        <span className="text-xs bg-slate-100 text-slate-700 font-mono px-2 py-1 rounded border border-slate-200">
          corr-db-9842
        </span>
      </div>

      <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {timeline && timeline.map((event, idx) => (
          <div key={idx} className="relative group">
            {/* Timeline dot */}
            <div className={`absolute -left-[27px] top-1 w-3 h-3 rounded-full border-2 border-white ring-2 ${
              event.severity === 'CRITICAL' ? 'bg-red-500 ring-red-200' :
              event.severity === 'ERROR' ? 'bg-red-400 ring-red-100' :
              event.severity === 'WARNING' ? 'bg-amber-500 ring-amber-200' :
              'bg-blue-500 ring-blue-200'
            }`} />

            <div className="p-3.5 rounded-lg border border-slate-200 bg-white group-hover:border-slate-300 group-hover:shadow-xs transition-all">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <Badge variant={event.severity} size="sm">
                    {event.severity}
                  </Badge>
                  <span className="font-mono text-xs text-slate-700 font-semibold bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                    {event.server}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">
                    {event.service}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-slate-400 font-mono text-[11px]">
                  <Clock className="w-3 h-3" />
                  <span>{event.time}</span>
                </div>
              </div>
              <p className="text-xs text-slate-800 font-mono leading-relaxed">
                {event.event}
              </p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
