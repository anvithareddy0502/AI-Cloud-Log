import React, { useState, useEffect } from 'react';
import ReportsTable from '../components/reports/ReportsTable';
import ReportPreviewModal from '../components/reports/ReportPreviewModal';
import { api } from '../services/api';
import { FileText, Download, Plus } from 'lucide-react';
import Button from '../components/common/Button';
import { useApp } from '../context/AppContext';

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const { showToast } = useApp();

  const loadReports = async () => {
    try {
      const data = await api.getReports();
      setReports(data || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleView = (rep) => {
    setActiveReport(rep);
    setModalOpen(true);
  };

  const handleDownload = (rep) => {
    const textContent = `
========================================================================
AI-CLAR INCIDENT POST-MORTEM REPORT
========================================================================
Report ID: ${rep.id}
Incident ID: ${rep.incident_id}
Title: ${rep.title}
Severity: ${rep.severity}
Server: ${rep.server}
Service: ${rep.service}
Generated Date: ${rep.date}
Author: ${rep.author || 'AI-CLAR Automated RCA Engine'}

SUMMARY:
${rep.summary}

ROOT CAUSE:
${rep.likely_root_cause}

IMPACT:
${rep.impact_scope}

MITIGATION RUNBOOK:
${(rep.mitigation_steps || []).map((s, idx) => `${idx + 1}. ${s}`).join('\n')}
`;
    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Incident_Report_${rep.id}.txt`;
    link.click();
    URL.revokeObjectURL(url);
    showToast(`Downloaded post-mortem report ${rep.id}`, 'info');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Incident Post-Mortem Reports
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated RCA post-mortems, executive incident briefings, and mitigation audit trails
          </p>
        </div>
      </div>

      {/* Reports Table */}
      <ReportsTable
        reports={reports}
        onViewReport={handleView}
        onDownloadReport={handleDownload}
      />

      {/* Modal */}
      <ReportPreviewModal
        report={activeReport}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </div>
  );
}
