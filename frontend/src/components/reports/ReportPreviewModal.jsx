import React from 'react';
import Modal from '../common/Modal';
import Badge from '../common/Badge';
import Button from '../common/Button';
import { Download, FileText, Server, Clock, CheckCircle } from 'lucide-react';
import { api } from '../../services/api';

export default function ReportPreviewModal({ report, isOpen, onClose }) {
  if (!report) return null;

  const handleDownload = () => {
    const textContent = `
========================================================================
AI-CLAR INCIDENT POST-MORTEM REPORT
========================================================================
Report ID: ${report.id}
Incident ID: ${report.incident_id}
Title: ${report.title}
Severity: ${report.severity}
Server: ${report.server}
Service: ${report.service}
Generated Date: ${report.date}
Author: ${report.author || 'AI-CLAR Automated RCA Engine'}

EXECUTIVE SUMMARY:
------------------------------------------------------------------------
${report.summary}

LIKELY ROOT CAUSE:
------------------------------------------------------------------------
${report.likely_root_cause}

IMPACT SCOPE:
------------------------------------------------------------------------
${report.impact_scope}

RECOMMENDED MITIGATION STEPS:
------------------------------------------------------------------------
${(report.mitigation_steps || []).map((step, idx) => `${idx + 1}. ${step}`).join('\n')}

========================================================================
Validated by AI-CLAR Cloud Root-Cause Analysis System
========================================================================
`;
    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `AI-CLAR-Report-${report.id}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadPdf = () => {
    const incId = report.incident_id || report.id;
    api.downloadIncidentReport(incId);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Incident Post-Mortem Report" maxWidth="max-w-3xl">
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={report.severity} dot size="sm">
                {report.severity}
              </Badge>
              <span className="text-xs font-mono text-slate-400">ID: {report.id}</span>
              <span className="text-xs text-slate-500">Date: {report.date}</span>
            </div>
            <h3 className="text-base font-bold text-slate-900">{report.title}</h3>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={Download}
              onClick={handleDownload}
            >
              Export TXT
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={FileText}
              onClick={handleDownloadPdf}
            >
              Download PDF Report
            </Button>
          </div>
        </div>

        {/* Executive Summary */}
        <div>
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Executive Summary
          </h4>
          <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3.5 rounded-lg border border-slate-200">
            {report.summary}
          </p>
        </div>

        {/* Root Cause & Scope */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-white border border-slate-200 rounded-lg">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
              Likely Root Cause
            </span>
            <p className="text-xs font-bold text-slate-900">
              {report.likely_root_cause}
            </p>
          </div>
          <div className="p-4 bg-white border border-slate-200 rounded-lg">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
              Impact Scope
            </span>
            <p className="text-xs font-medium text-slate-800">
              {report.impact_scope}
            </p>
          </div>
        </div>

        {/* Mitigation Steps */}
        {report.mitigation_steps && (
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Action Runbook & Mitigation
            </h4>
            <div className="space-y-2">
              {report.mitigation_steps.map((step, idx) => (
                <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-700 bg-slate-50/70 p-2.5 rounded border border-slate-200">
                  <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
          <span>Author: {report.author}</span>
          <span>Status: Verified</span>
        </div>
      </div>
    </Modal>
  );
}
