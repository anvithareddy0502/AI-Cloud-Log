import React, { useState, useRef } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, Sparkles, RefreshCw, X } from 'lucide-react';
import { api } from '../../services/api';
import { useApp } from '../../context/AppContext';

export default function UploadLogModal({ isOpen, onClose, onSuccess }) {
  const { refreshCounts } = useApp();
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setResult(null);
      setErrorMessage(null);
      setUploadProgress(0);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      setFile(dropped);
      setResult(null);
      setErrorMessage(null);
      setUploadProgress(0);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleUpload = async () => {
    if (!file || isUploading) return;
    setIsUploading(true);
    setUploadProgress(30);
    setErrorMessage(null);

    try {
      // Simulate stepped progress
      const progressTimer = setInterval(() => {
        setUploadProgress((prev) => (prev < 85 ? prev + 15 : prev));
      }, 150);

      const res = await api.uploadLogs(file);
      clearInterval(progressTimer);
      setUploadProgress(100);
      setResult(res);
      if (refreshCounts) {
        refreshCounts();
      }
    } catch (err) {
      setErrorMessage(err.message || 'Failed to upload and process logs.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    const hadResult = !!result;
    setFile(null);
    setResult(null);
    setErrorMessage(null);
    setUploadProgress(0);
    onClose();
    if (hadResult) {
      if (refreshCounts) refreshCounts();
      if (onSuccess) onSuccess();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Upload Cloud Logs" maxWidth="max-w-xl">
      <div className="space-y-5">
        {/* Upload State or Result State */}
        {!result ? (
          <>
            {/* Drop Zone */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-200 hover:border-blue-400 rounded-lg p-6 text-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-blue-50/30"
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".log,.txt,.csv,.json"
                className="hidden"
              />
              <UploadCloud className="w-10 h-10 text-blue-600 mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-800">
                Click to browse or drag & drop logs here
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Supports <span className="font-mono text-slate-700">.log, .txt, .csv, .json</span> (Max 25MB)
              </p>
            </div>

            {/* Selected File Details */}
            {file && (
              <div className="flex items-center justify-between p-3.5 bg-white border border-slate-200 rounded-lg shadow-xs">
                <div className="flex items-center gap-2.5 min-w-0">
                  <FileText className="w-5 h-5 text-blue-600 shrink-0" />
                  <div className="truncate">
                    <p className="text-xs font-semibold text-slate-800 truncate">{file.name}</p>
                    <p className="text-[11px] text-slate-400">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                {!isUploading && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    className="text-slate-400 hover:text-slate-600 p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}

            {/* Progress bar */}
            {isUploading && (
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium text-slate-600">
                  <span>Processing, extracting features & detecting ML anomalies...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-blue-600 h-full rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Error Message */}
            {errorMessage && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2.5 text-xs text-red-700">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">Upload Failed</span>
                  <span>{errorMessage}</span>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button variant="secondary" size="md" onClick={handleClose} disabled={isUploading}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="md"
                onClick={handleUpload}
                disabled={!file || isUploading}
                icon={isUploading ? RefreshCw : UploadCloud}
              >
                {isUploading ? 'Processing...' : 'Upload & Process'}
              </Button>
            </div>
          </>
        ) : (
          /* Processing Results Summary */
          <div className="space-y-5">
            <div className="flex items-center gap-2 text-emerald-700 bg-emerald-50 border border-emerald-200/80 p-3 rounded-lg text-xs">
              <CheckCircle2 className="w-5 h-5 shrink-0" />
              <div>
                <span className="font-bold text-sm block text-emerald-900">
                  Log Ingestion & Anomaly Analysis Complete
                </span>
                <span>The telemetry pipeline processed the file and updated cluster models.</span>
              </div>
            </div>

            {/* 4 Summary Metric Boxes */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Total Logs
                </span>
                <span className="text-xl font-bold text-slate-900 mt-1 block font-mono">
                  {result.total_records}
                </span>
              </div>

              <div className="p-3 bg-emerald-50/60 border border-emerald-200/80 rounded-lg">
                <span className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider block">
                  Parsed Logs
                </span>
                <span className="text-xl font-bold text-emerald-800 mt-1 block font-mono">
                  {result.successfully_parsed}
                </span>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Failed Lines
                </span>
                <span className={`text-xl font-bold mt-1 block font-mono ${
                  result.failed_records > 0 ? 'text-amber-600' : 'text-slate-600'
                }`}>
                  {result.failed_records}
                </span>
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <span className="text-[11px] font-semibold text-blue-700 uppercase tracking-wider block flex items-center justify-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  Anomalies
                </span>
                <span className="text-xl font-bold text-blue-800 mt-1 block font-mono">
                  {result.anomalies_detected}
                </span>
              </div>
            </div>

            {/* Errors breakdown if any lines failed */}
            {result.errors && result.errors.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Skipped Line Diagnostics ({result.errors.length}):
                </span>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 max-h-28 overflow-y-auto font-mono text-[11px] text-slate-600 divide-y divide-slate-200">
                  {result.errors.map((err, i) => (
                    <div key={i} className="py-1">{err}</div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <Button variant="primary" size="md" onClick={handleClose}>
                Done & Refresh Dashboard
              </Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
