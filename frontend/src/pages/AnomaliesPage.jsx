import React, { useState, useEffect } from 'react';
import AnomalyCard from '../components/anomalies/AnomalyCard';
import { api } from '../services/api';
import { AlertTriangle, Sparkles, Filter, RefreshCw } from 'lucide-react';
import Button from '../components/common/Button';

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const res = await api.getAnomalies();
      setAnomalies(res || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, []);

  const filtered = filterSeverity === 'ALL'
    ? anomalies
    : anomalies.filter(a => a.severity.toUpperCase() === filterSeverity);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              AI Detected Anomalies
            </h1>
            <span className="text-[10px] font-semibold uppercase tracking-wider bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200">
              Isolation Forest + Heuristics
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Statistical metric deviations, error rate surges, and anomalous cluster behavioral patterns
          </p>
        </div>

        {/* Severity Filter Tabs */}
        <div className="flex items-center gap-2 bg-slate-50 p-1 rounded-lg border border-slate-200">
          {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
                filterSeverity === sev
                  ? 'bg-white text-slate-900 shadow-xs border border-slate-200/80'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Anomalies List */}
      <div className="space-y-3">
        {filtered.length > 0 ? (
          filtered.map((item) => (
            <AnomalyCard key={item.id} anomaly={item} />
          ))
        ) : (
          <div className="p-12 text-center bg-white border border-slate-200 rounded-lg text-xs text-slate-400">
            No anomalies found for the selected severity level.
          </div>
        )}
      </div>
    </div>
  );
}
