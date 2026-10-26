import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import AppLayout from './components/layout/AppLayout';
import DashboardPage from './pages/DashboardPage';
import LiveLogsPage from './pages/LiveLogsPage';
import AnomaliesPage from './pages/AnomaliesPage';
import IncidentAnalysisPage from './pages/IncidentAnalysisPage';
import SecurityPage from './pages/SecurityPage';
import AssistantPage from './pages/AssistantPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';

function AppContent() {
  const { activeTab } = useApp();

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage />;
      case 'logs':
        return <LiveLogsPage />;
      case 'anomalies':
        return <AnomaliesPage />;
      case 'incidents':
        return <IncidentAnalysisPage />;
      case 'security':
        return <SecurityPage />;
      case 'assistant':
        return <AssistantPage />;
      case 'reports':
        return <ReportsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DashboardPage />;
    }
  };

  return <AppLayout>{renderActivePage()}</AppLayout>;
}

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
