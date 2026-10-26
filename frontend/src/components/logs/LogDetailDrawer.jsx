import React, { useState } from 'react';
import Drawer from '../common/Drawer';
import Badge from '../common/Badge';
import Button from '../common/Button';
import { Copy, Check, Terminal, Server, Layers, Cpu, Globe, Hash } from 'lucide-react';

export default function LogDetailDrawer({ log, isOpen, onClose }) {
  const [copied, setCopied] = useState(false);

  if (!log) return null;

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(log, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Drawer isOpen={isOpen} onClose={onClose} title="Cloud Log Telemetry Inspector">
      <div className="space-y-6">
        {/* Top Summary */}
        <div className="flex items-center justify-between">
          <Badge variant={log.severity} dot size="md">
            {log.severity}
          </Badge>
          <span className="text-xs font-mono text-slate-500">{log.timestamp}</span>
        </div>

        {/* Message Banner */}
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Log Message
          </p>
          <p className="text-sm font-mono text-slate-900 break-words leading-relaxed">
            {log.message}
          </p>
        </div>

        {/* Metadata Grid */}
        <div>
          <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-3">
            Event Context & Topology
          </h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                <Server className="w-3.5 h-3.5" />
                <span>Compute Node</span>
              </div>
              <p className="text-xs font-semibold font-mono text-slate-800">{log.server}</p>
            </div>

            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                <Layers className="w-3.5 h-3.5" />
                <span>Service / Subsystem</span>
              </div>
              <p className="text-xs font-semibold text-slate-800">{log.service}</p>
            </div>

            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                <Hash className="w-3.5 h-3.5" />
                <span>Correlation ID</span>
              </div>
              <p className="text-xs font-mono text-blue-600 font-medium truncate">
                {log.correlation_id || 'N/A'}
              </p>
            </div>

            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                <Globe className="w-3.5 h-3.5" />
                <span>Source IP / Latency</span>
              </div>
              <p className="text-xs font-mono text-slate-800">
                {log.ip_address || '10.0.1.1'} ({log.latency_ms ? `${log.latency_ms}ms` : 'N/A'})
              </p>
            </div>
          </div>
        </div>

        {/* Stack Trace (if present) */}
        {log.stack_trace && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-red-700 uppercase tracking-wider flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5" />
                Exception Stack Trace
              </span>
            </div>
            <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed">
              {log.stack_trace}
            </pre>
          </div>
        )}

        {/* Raw JSON viewer */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
              Structured JSON Payload
            </span>
            <Button
              variant="secondary"
              size="sm"
              icon={copied ? Check : Copy}
              onClick={handleCopyJson}
            >
              {copied ? 'Copied' : 'Copy JSON'}
            </Button>
          </div>
          <pre className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800 overflow-x-auto max-h-56 leading-relaxed">
            {JSON.stringify(log, null, 2)}
          </pre>
        </div>
      </div>
    </Drawer>
  );
}
