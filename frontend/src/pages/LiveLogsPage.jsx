import React, { useState, useEffect } from 'react';
import LogFilterBar from '../components/logs/LogFilterBar';
import LogTable from '../components/logs/LogTable';
import LogDetailDrawer from '../components/logs/LogDetailDrawer';
import UploadLogModal from '../components/logs/UploadLogModal';
import { api } from '../services/api';
import { RefreshCw, Download, UploadCloud } from 'lucide-react';
import Button from '../components/common/Button';
import { useApp } from '../context/AppContext';

export default function LiveLogsPage() {
  const { showToast } = useApp();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedServer, setSelectedServer] = useState('All');
  const [selectedSeverity, setSelectedSeverity] = useState('All');
  const [selectedService, setSelectedService] = useState('All');
  const [selectedTimeRange, setSelectedTimeRange] = useState('Last 24h');
  const [activeLog, setActiveLog] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await api.getLogs({
        server: selectedServer,
        service: selectedService,
        severity: selectedSeverity,
        search: searchQuery,
        time_range: selectedTimeRange,
      });
      setLogs(res?.logs || []);
    } catch (err) {
      console.error("Error fetching logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [selectedServer, selectedSeverity, selectedService, selectedTimeRange, searchQuery]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedServer('All');
    setSelectedSeverity('All');
    setSelectedService('All');
    setSelectedTimeRange('Last 24h');
  };

  const handleSelectLog = (log) => {
    setActiveLog(log);
    setDrawerOpen(true);
  };

  const handleExportCsv = () => {
    if (!logs.length) return;
    const header = ['ID', 'Timestamp', 'Server', 'Service', 'Severity', 'Message', 'Correlation_ID'];
    const rows = logs.map(l => [
      l.id,
      `"${l.timestamp}"`,
      `"${l.server}"`,
      `"${l.service}"`,
      `"${l.severity}"`,
      `"${l.message.replace(/"/g, '""')}"`,
      `"${l.correlation_id || ''}"`
    ]);
    const csvContent = [header.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `cloud_logs_${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Live Cloud Logs</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time streaming logs from production microservices, proxies, and database nodes
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="primary"
            size="sm"
            icon={UploadCloud}
            onClick={() => setUploadModalOpen(true)}
          >
            Upload Logs
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={Download}
            onClick={handleExportCsv}
          >
            Export Logs (CSV)
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={RefreshCw}
            onClick={fetchLogs}
            disabled={loading}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <LogFilterBar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        selectedServer={selectedServer}
        setSelectedServer={setSelectedServer}
        selectedSeverity={selectedSeverity}
        setSelectedSeverity={setSelectedSeverity}
        selectedService={selectedService}
        setSelectedService={setSelectedService}
        selectedTimeRange={selectedTimeRange}
        setSelectedTimeRange={setSelectedTimeRange}
        onReset={handleResetFilters}
      />

      {/* Log Table */}
      <LogTable logs={logs} onSelectLog={handleSelectLog} />

      {/* Drawer */}
      <LogDetailDrawer
        log={activeLog}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

      {/* Upload Log Modal */}
      <UploadLogModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={() => {
          fetchLogs();
          showToast("Cloud logs ingested & ML telemetry models updated", "success");
        }}
      />
    </div>
  );
}
