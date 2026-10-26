import React from 'react';
import AssistantChat from '../components/assistant/AssistantChat';

export default function AssistantPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">AI Cloud Assistant</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Natural-language diagnostics interface for querying multi-node cloud clusters and incident root causes
        </p>
      </div>

      <AssistantChat />
    </div>
  );
}
