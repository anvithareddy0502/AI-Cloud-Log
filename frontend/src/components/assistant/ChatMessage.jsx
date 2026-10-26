import React from 'react';
import Badge from '../common/Badge';
import { Bot, User, Server, Flame, Sparkles, CheckCircle2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function ChatMessage({ message, onSelectFollowup }) {
  const { navigateToIncident } = useApp();
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs mt-0.5">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div className={`max-w-2xl rounded-lg p-4 text-xs leading-relaxed space-y-3 ${
        isUser
          ? 'bg-blue-600 text-white shadow-xs'
          : 'bg-white border border-slate-200 text-slate-800 shadow-xs'
      }`}>
        {/* Author Header */}
        <div className="flex items-center justify-between gap-4 border-b pb-2 text-[10px] uppercase tracking-wider font-semibold opacity-75">
          <span>{isUser ? 'You (DevOps Engineer)' : 'AI-CLAR Cloud Assistant'}</span>
          <span>{message.timestamp}</span>
        </div>

        {/* Text body */}
        <div className="whitespace-pre-line text-xs font-normal">
          {message.content}
        </div>

        {/* Evidence & Telemetry metadata if provided */}
        {message.key_evidence && message.key_evidence.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Correlated Telemetry Evidence
            </span>
            {message.key_evidence.map((ev, i) => (
              <div key={i} className="flex items-center gap-1.5 text-slate-700 bg-slate-50 px-2 py-1 rounded text-[11px]">
                <CheckCircle2 className="w-3 h-3 text-blue-600 shrink-0" />
                <span>{ev}</span>
              </div>
            ))}
          </div>
        )}

        {/* Actionable Drilldowns */}
        {!isUser && (message.related_server || message.related_incident_id) && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
            {message.related_server && (
              <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[11px] font-mono border border-slate-200">
                <Server className="w-3 h-3 text-slate-400" />
                {message.related_server}
              </span>
            )}
            {message.related_incident_id && (
              <button
                onClick={() => navigateToIncident(message.related_incident_id)}
                className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800 hover:underline bg-blue-50 px-2 py-0.5 rounded border border-blue-200"
              >
                <Flame className="w-3 h-3 text-red-500" />
                Inspect Root Cause
              </button>
            )}
            {message.confidence_score && (
              <span className="text-[11px] text-slate-400 font-medium ml-auto">
                Confidence: {message.confidence_score}%
              </span>
            )}
          </div>
        )}

        {/* Followups */}
        {!isUser && message.suggested_followups && message.suggested_followups.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-2">
            {message.suggested_followups.map((f, i) => (
              <button
                key={i}
                onClick={() => onSelectFollowup(f)}
                className="text-[11px] bg-slate-50 hover:bg-slate-100 text-slate-600 font-medium px-2.5 py-1 rounded-md border border-slate-200 transition-colors"
              >
                &rarr; {f}
              </button>
            ))}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 mt-0.5 border border-slate-300 font-bold text-xs">
          ME
        </div>
      )}
    </div>
  );
}
