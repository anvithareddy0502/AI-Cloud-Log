import React, { useState } from 'react';
import {
  Cloud,
  Bell,
  CheckCircle2,
  ChevronDown,
  Wifi,
  ExternalLink,
  Shield,
  Layers
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function TopBar() {
  const {
    activeTab,
    activeEnvironment,
    setActiveEnvironment,
    notifications,
    setNotifications,
    navigateToIncident
  } = useApp();

  const [showNotifications, setShowNotifications] = useState(false);

  const environments = [
    'AWS Production (us-east-1)',
    'AWS Staging (us-west-2)',
    'GCP Multi-region Cluster'
  ];

  const unreadCount = notifications.filter(n => n.unread).length;

  const markAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  const pageTitles = {
    dashboard: 'Cloud Observability Dashboard',
    logs: 'Live Cloud Logs Explorer',
    anomalies: 'AI Detected Anomalies',
    incidents: 'Root-Cause & Incident Analysis',
    security: 'Cloud Security & Access Audit',
    assistant: 'AI Cloud Assistant',
    reports: 'Incident Post-Mortem Reports',
    settings: 'Platform & Cluster Settings'
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Breadcrumb / Active Page Title */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
          AI-CLAR
        </span>
        <span className="text-slate-300">/</span>
        <h1 className="text-sm font-semibold text-slate-800">
          {pageTitles[activeTab] || 'Dashboard'}
        </h1>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4">
        {/* Environment Selector */}
        <div className="relative flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-md px-3 py-1.5 text-xs">
          <Cloud className="w-3.5 h-3.5 text-slate-500" />
          <select
            value={activeEnvironment}
            onChange={(e) => setActiveEnvironment(e.target.value)}
            className="bg-transparent border-none p-0 pr-4 font-medium text-slate-700 cursor-pointer focus:outline-none text-xs"
          >
            {environments.map((env) => (
              <option key={env} value={env}>
                {env}
              </option>
            ))}
          </select>
        </div>

        {/* Live Telemetry Status Pill */}
        <div className="hidden md:flex items-center gap-2 px-2.5 py-1 bg-emerald-50/70 border border-emerald-200/80 rounded-full text-xs text-emerald-700 font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Live Ingestion Active</span>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-md text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors relative"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white" />
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-slate-200 py-2 z-50">
              <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-900">Incident Alerts</span>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    className="text-[11px] text-blue-600 hover:underline font-medium"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-64 overflow-y-auto divide-y divide-slate-100">
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    onClick={() => {
                      if (notif.severity === 'critical') navigateToIncident('inc-01');
                      setShowNotifications(false);
                    }}
                    className={`p-3 text-xs hover:bg-slate-50 cursor-pointer ${
                      notif.unread ? 'bg-blue-50/30' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between text-slate-500 mb-1">
                      <span className="font-mono text-[10px]">{notif.server}</span>
                      <span className="text-[10px]">{notif.time}</span>
                    </div>
                    <p className="text-xs font-medium text-slate-800 leading-snug">
                      {notif.title}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Pill */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
          <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 font-semibold flex items-center justify-center text-xs border border-blue-200">
            A
          </div>
          <span className="text-xs font-medium text-slate-700 hidden sm:inline-block">
            Admin
          </span>
        </div>
      </div>
    </header>
  );
}
