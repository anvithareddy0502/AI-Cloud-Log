import React from 'react';
import {
  LayoutDashboard,
  ScrollText,
  AlertTriangle,
  Flame,
  ShieldAlert,
  Bot,
  FileText,
  Settings as SettingsIcon,
  Activity,
  CheckCircle2,
  Server
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export default function Sidebar() {
  const { activeTab, setActiveTab, counts } = useApp();

  const anomaliesBadge = counts?.anomalies !== null && counts?.anomalies !== undefined 
    ? String(counts.anomalies) 
    : null;
    
  const incidentsBadge = counts?.incidents !== null && counts?.incidents !== undefined 
    ? String(counts.incidents) 
    : null;

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'logs', label: 'Live Logs', icon: ScrollText },
    { id: 'anomalies', label: 'AI Anomalies', icon: AlertTriangle, badge: anomaliesBadge },
    { id: 'incidents', label: 'Incidents', icon: Flame, badge: incidentsBadge, badgeColor: 'bg-red-100 text-red-700' },
    { id: 'security', label: 'Security', icon: ShieldAlert },
    { id: 'assistant', label: 'AI Assistant', icon: Bot, isNew: true },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between select-none h-screen sticky top-0">
      {/* Brand Header */}
      <div>
        <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-slate-900 tracking-tight text-base">AI-CLAR</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                Cloud
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-normal truncate max-w-[140px]">
              Log Correlation & RCA
            </p>
          </div>
        </div>

        {/* Nav links */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Monitoring & AI
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50/80 text-blue-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge !== null && (
                  <span
                    className={`text-[11px] px-1.5 py-0.5 rounded font-medium ${
                      item.badgeColor || 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
                {item.isNew && (
                  <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded">
                    GenAI
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Profile & Status */}
      <div className="p-3 border-t border-slate-100 space-y-3 bg-slate-50/40">
        {/* Connection Status */}
        <div className="flex items-center justify-between px-3 py-1.5 rounded-md bg-white border border-slate-200/80 text-xs">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-slate-600 font-medium">System Status</span>
          </div>
          <span className="text-emerald-700 font-medium text-[11px] bg-emerald-50 px-1.5 py-0.5 rounded">
            Connected
          </span>
        </div>

        {/* User Card */}
        <div className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white transition-colors cursor-pointer">
          <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 font-semibold flex items-center justify-center text-xs border border-slate-300">
            AD
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-800 truncate">Admin</p>
            <p className="text-[11px] text-slate-400 truncate">Cloud DevOps Lead</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
