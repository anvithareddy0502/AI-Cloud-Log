import React from 'react';
import { Search, RotateCcw, Server, ShieldAlert, Layers, Clock } from 'lucide-react';
import FilterDropdown from '../common/FilterDropdown';
import Button from '../common/Button';

export default function LogFilterBar({
  searchQuery,
  setSearchQuery,
  selectedServer,
  setSelectedServer,
  selectedSeverity,
  setSelectedSeverity,
  selectedService,
  setSelectedService,
  selectedTimeRange,
  setSelectedTimeRange,
  onReset
}) {
  const serverOptions = ['All', 'Server-01', 'Server-02', 'Server-03', 'Server-04', 'Server-05', 'Server-06'];
  const severityOptions = ['All', 'CRITICAL', 'ERROR', 'WARNING', 'INFO'];
  const serviceOptions = ['All', 'Database', 'Payment API', 'Authentication', 'Web Server', 'Network', 'Cache'];
  const timeRangeOptions = ['Last 15m', 'Last 1h', 'Last 24h', 'Last 7d'];

  return (
    <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-white p-4 rounded-lg border border-slate-200 shadow-xs mb-4">
      {/* Search Input */}
      <div className="relative flex-1 min-w-[240px]">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search logs by message, correlation ID, server..."
          className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-mono"
        />
      </div>

      {/* Filter Dropdowns */}
      <div className="flex flex-wrap items-center gap-2">
        <FilterDropdown
          label="Server"
          icon={Server}
          value={selectedServer}
          options={serverOptions}
          onChange={setSelectedServer}
        />

        <FilterDropdown
          label="Severity"
          icon={ShieldAlert}
          value={selectedSeverity}
          options={severityOptions}
          onChange={setSelectedSeverity}
        />

        <FilterDropdown
          label="Service"
          icon={Layers}
          value={selectedService}
          options={serviceOptions}
          onChange={setSelectedService}
        />

        <FilterDropdown
          label="Time"
          icon={Clock}
          value={selectedTimeRange}
          options={timeRangeOptions}
          onChange={setSelectedTimeRange}
        />

        <Button
          variant="secondary"
          size="sm"
          icon={RotateCcw}
          onClick={onReset}
          className="text-slate-500 hover:text-slate-700"
        >
          Reset
        </Button>
      </div>
    </div>
  );
}
