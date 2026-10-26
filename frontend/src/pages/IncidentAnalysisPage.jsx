import React, { useState, useEffect } from 'react';
import IncidentHeader from '../components/incidents/IncidentHeader';
import AiExplanationBox from '../components/incidents/AiExplanationBox';
import EvidenceList from '../components/incidents/EvidenceList';
import RootCauseCard from '../components/incidents/RootCauseCard';
import RecommendedActions from '../components/incidents/RecommendedActions';
import CorrelationTimeline from '../components/incidents/CorrelationTimeline';
import ReportPreviewModal from '../components/reports/ReportPreviewModal';
import { api } from '../services/api';
import { useApp } from '../context/AppContext';
import { RefreshCw, AlertCircle } from 'lucide-react';

export default function IncidentAnalysisPage() {
  const { selectedIncidentId, setSelectedIncidentId, showToast, refreshCounts } = useApp();
  const [incidentsList, setIncidentsList] = useState([]);
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeReport, setActiveReport] = useState(null);
  const [reportModalOpen, setReportModalOpen] = useState(false);

  const loadAllIncidents = async () => {
    setRefreshing(true);
    try {
      const all = await api.getIncidents();
      const list = all || [];
      setIncidentsList(list);
      if (list.length > 0 && (!selectedIncidentId || !list.some(i => (i.id === selectedIncidentId || i.incident_id === selectedIncidentId)))) {
        setSelectedIncidentId(list[0].id || list[0].incident_id);
      }
    } catch (err) {
      console.error("Failed to load incidents list:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAllIncidents();
  }, []);

  // Load selected incident details
  useEffect(() => {
    async function loadSelected() {
      if (!selectedIncidentId) return;
      setLoading(true);
      try {
        const item = await api.getIncidentById(selectedIncidentId);
        setIncident(item);
      } catch (err) {
        console.error("Failed to load incident details:", err);
      } finally {
        setLoading(false);
      }
    }
    loadSelected();
  }, [selectedIncidentId]);

  const handleStatusChange = async (newStatus) => {
    if (!incident) return;
    const incId = incident.id || incident.incident_id;
    try {
      await api.updateIncidentStatus(incId, newStatus);
      setIncident(prev => ({ ...prev, status: newStatus }));
      setIncidentsList(prev => prev.map(i => ((i.id === incId || i.incident_id === incId) ? { ...i, status: newStatus } : i)));
      showToast(`Incident status updated to ${newStatus}`, 'success');
      if (refreshCounts) refreshCounts();
    } catch (err) {
      console.error("Status update error:", err);
      showToast('Failed to update status', 'error');
    }
  };

  const handleResolve = async () => {
    if (!incident) return;
    const incId = incident.id || incident.incident_id;
    try {
      await api.resolveIncident(incId);
      setIncident(prev => ({ ...prev, status: 'RESOLVED' }));
      setIncidentsList(prev => prev.map(i => ((i.id === incId || i.incident_id === incId) ? { ...i, status: 'RESOLVED' } : i)));
      showToast(`Incident ${incId} marked as RESOLVED`, 'success');
      if (refreshCounts) refreshCounts();
    } catch (err) {
      console.error("Resolve incident error:", err);
      showToast('Failed to resolve incident', 'error');
    }
  };

  const handleIgnore = async () => {
    if (!incident) return;
    const incId = incident.id || incident.incident_id;
    try {
      await api.ignoreIncident(incId);
      setIncident(prev => ({ ...prev, status: 'IGNORED' }));
      setIncidentsList(prev => prev.map(i => ((i.id === incId || i.incident_id === incId) ? { ...i, status: 'IGNORED' } : i)));
      showToast(`Incident ${incId} marked as IGNORED`, 'info');
      if (refreshCounts) refreshCounts();
    } catch (err) {
      console.error("Ignore incident error:", err);
      showToast('Failed to ignore incident', 'error');
    }
  };

  const handleGenerateReport = async () => {
    if (!incident) return;
    const incId = incident.id || incident.incident_id;
    try {
      showToast('Downloading official PDF Incident Report...', 'info');
      api.downloadIncidentReport(incId);
      const report = await api.generateReport(incId);
      setActiveReport(report);
      setReportModalOpen(true);
      showToast('PDF Report downloaded & preview opened', 'success');
    } catch (err) {
      console.error("Report generation error:", err);
      showToast('Failed to generate report', 'error');
    }
  };

  if (!incident && loading) {
    return (
      <div className="p-16 text-center text-xs text-slate-500 bg-white border border-slate-200 rounded-lg">
        <RefreshCw className="w-5 h-5 mx-auto mb-2 text-blue-600 animate-spin" />
        Loading root-cause telemetry and causal graph...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Selector Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Incident Root-Cause Analysis (RCA)
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Causal dependency graph, correlated log timelines, and automated remediation runbooks
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {/* Refresh Button */}
          <button
            onClick={loadAllIncidents}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-3 py-1.5 rounded-md shadow-xs transition-colors"
            title="Refresh incidents telemetry"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          {/* Quick incident switcher */}
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-md px-3 py-1.5 shadow-xs text-xs">
            <span className="text-slate-400 font-medium">Select Incident:</span>
            <select
              value={selectedIncidentId}
              onChange={(e) => setSelectedIncidentId(e.target.value)}
              className="bg-transparent border-none p-0 pr-4 font-semibold text-slate-800 cursor-pointer focus:outline-none text-xs"
            >
              {incidentsList.map((inc) => (
                <option key={inc.id || inc.incident_id} value={inc.id || inc.incident_id}>
                  {inc.title} ({inc.affected_server}) [{inc.status}]
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {incident ? (
        <>
          {/* Main Incident Banner with Resolve & Ignore actions */}
          <IncidentHeader
            incident={incident}
            onGenerateReport={handleGenerateReport}
            onStatusChange={handleStatusChange}
            onResolve={handleResolve}
            onIgnore={handleIgnore}
          />

          {/* AI Analysis Explanation Section */}
          <AiExplanationBox incident={incident} summary={incident.ai_summary} />

          {/* Core RCA & Confidence */}
          <RootCauseCard
            rootCause={incident.likely_root_cause || incident.root_cause}
            confidence={incident.confidence}
          />

          {/* Evidence Grid & Timeline */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <EvidenceList evidence={incident.evidence} />
            <RecommendedActions actions={incident.recommended_actions || incident.recommendations} />
          </div>

          {/* Correlated Event Sequence Timeline */}
          <CorrelationTimeline timeline={incident.timeline} />
        </>
      ) : (
        <div className="p-12 text-center text-xs text-slate-500 bg-white border border-slate-200 rounded-lg">
          <AlertCircle className="w-6 h-6 mx-auto mb-2 text-slate-400" />
          No incident selected or available in database.
        </div>
      )}

      {/* Report Modal */}
      <ReportPreviewModal
        report={activeReport}
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
      />
    </div>
  );
}
