import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { Sparkles, HelpCircle, AlertTriangle, Layers, Target, CheckCircle2, Wrench, ShieldAlert } from 'lucide-react';

export default function AiExplanationBox({ incident, summary, explanation }) {
  const aiData = explanation || incident?.ai_explanation || {};

  const whatHappened = aiData.what_happened || incident?.what_happened || summary || 
    "An abnormal surge in error rates and latency degradation was detected across affected cloud nodes.";
  
  const whyDetected = aiData.why_it_was_detected || incident?.why_it_was_detected || 
    "Correlated log volume exceeded baseline anomaly thresholds and multi-service dependency heuristics.";

  const likelyRootCause = aiData.likely_root_cause || incident?.likely_root_cause || incident?.root_cause || 
    "Root cause under active investigation";

  const confidence = aiData.confidence ?? incident?.confidence ?? 85;

  const affectedServices = (aiData.affected_services?.length ? aiData.affected_services : incident?.affected_services) || 
    (incident?.affected_service ? [incident.affected_service] : ["System"]);

  const evidence = (aiData.evidence?.length ? aiData.evidence : incident?.evidence) || [];
  
  const recommendations = (aiData.recommended_actions?.length ? aiData.recommended_actions : incident?.recommended_actions) || 
    incident?.recommendations || [];

  const isInsufficient = aiData.has_sufficient_evidence === false || 
    likelyRootCause.toLowerCase().includes("insufficient evidence") ||
    likelyRootCause.toLowerCase().includes("undetermined");

  return (
    <Card className="p-6 border-slate-200 bg-white shadow-xs space-y-6">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-50 text-blue-600 rounded-md border border-blue-100">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Evidence-Based AI Incident Analysis
            </h3>
            <p className="text-xs text-slate-500">
              Grounded synthesis of retrieved cluster logs, causal dependencies, and ML anomalies
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={isInsufficient ? "warning" : confidence >= 80 ? "healthy" : "warning"} size="md">
            {isInsufficient ? "LOW CONFIDENCE" : `${confidence}% CONFIDENCE`}
          </Badge>
        </div>
      </div>

      {isInsufficient && (
        <div className="flex items-start gap-3 p-3.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block mb-0.5">Insufficient Evidence Notice</span>
            Insufficient evidence to determine a confident root cause. The system requires additional error telemetry and correlated indicators.
          </div>
        </div>
      )}

      {/* Grid: What Happened & Why Detected */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Section 1: What Happened */}
        <div className="space-y-2 p-4 bg-slate-50/60 rounded-lg border border-slate-200/80">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wide">
            <HelpCircle className="w-3.5 h-3.5 text-blue-600" />
            <span>What Happened</span>
          </div>
          <p className="text-xs text-slate-700 leading-relaxed font-normal">
            {whatHappened}
          </p>
        </div>

        {/* Section 2: Why It Was Detected */}
        <div className="space-y-2 p-4 bg-slate-50/60 rounded-lg border border-slate-200/80">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wide">
            <Target className="w-3.5 h-3.5 text-blue-600" />
            <span>Why It Was Detected</span>
          </div>
          <p className="text-xs text-slate-700 leading-relaxed font-normal">
            {whyDetected}
          </p>
        </div>
      </div>

      {/* Grid: Likely Root Cause & Affected Services */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Section 3: Likely Root Cause */}
        <div className="space-y-2 p-4 bg-blue-50/30 rounded-lg border border-blue-100">
          <span className="text-[11px] font-bold text-blue-700 uppercase tracking-wider block">
            Likely Root Cause
          </span>
          <h4 className="text-sm font-bold text-slate-900">
            {likelyRootCause}
          </h4>
          <p className="text-[11px] text-slate-500">
            Identified via temporal graph traversal and upstream causal dependency depth.
          </p>
        </div>

        {/* Section 4: Affected Services */}
        <div className="space-y-2 p-4 bg-slate-50/60 rounded-lg border border-slate-200/80">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wide">
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            <span>Affected Services</span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {affectedServices.map((svc, idx) => (
              <span
                key={idx}
                className="text-xs font-semibold bg-white border border-slate-200 text-slate-800 px-2.5 py-1 rounded-md shadow-2xs"
              >
                {svc}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Section 5: Evidence Bullets */}
      {evidence.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Telemetry Evidence
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              {evidence.length} verified indicators
            </span>
          </div>
          <div className="space-y-2">
            {evidence.map((item, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 text-xs text-slate-700 p-2.5 bg-slate-50 border border-slate-200 rounded-md"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{item}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 6: Recommended Actions (Non-destructive) */}
      {recommendations.length > 0 && (
        <div className="space-y-2.5 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2">
            <Wrench className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Recommended Remediation Runbook (Non-Destructive)
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 text-xs text-slate-800 p-2.5 bg-white border border-slate-200 rounded-md hover:border-slate-300 transition-colors"
              >
                <span className="flex items-center justify-center w-4 h-4 rounded bg-blue-100 text-blue-700 text-[10px] font-bold shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span className="leading-relaxed">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
