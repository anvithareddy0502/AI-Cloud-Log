import React from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { useApp } from '../../context/AppContext';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';

export default function AppLayout({ children }) {
  const { toast } = useApp();

  return (
    <div className="flex min-h-screen bg-white text-slate-900 font-sans antialiased">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />

        <main className="flex-1 px-4 py-4 sm:px-6 sm:py-5 bg-white overflow-y-auto max-w-6xl w-full mx-auto">
          {children}
        </main>
      </div>

      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2 bg-slate-900 text-white px-4 py-2.5 rounded-lg shadow-lg border border-slate-800 text-xs animate-in fade-in slide-in-from-bottom-2">
          {toast.type === 'success' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
          {toast.type === 'error' && <AlertCircle className="w-4 h-4 text-red-400" />}
          {toast.type === 'info' && <Info className="w-4 h-4 text-blue-400" />}
          <span className="font-medium">{toast.message}</span>
        </div>
      )}
    </div>
  );
}
