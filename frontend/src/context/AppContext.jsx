import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const AppContext = createContext();

export function AppProvider({ children }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedIncidentId, setSelectedIncidentId] = useState('inc-01');
  const [activeEnvironment, setActiveEnvironment] = useState('AWS Production (us-east-1)');
  const [toast, setToast] = useState(null);

  // Dynamic Telemetry Counts for Badges (Fetched from MongoDB)
  const [counts, setCounts] = useState({
    anomalies: null,
    incidents: null,
  });

  const refreshCounts = useCallback(async () => {
    try {
      const res = await api.getSystemCounts();
      if (res) {
        setCounts({
          anomalies: res.anomalies ?? res.total_anomalies ?? 0,
          incidents: res.incidents ?? res.total_incidents ?? res.active_incidents ?? 0,
        });
      }
    } catch (err) {
      console.error("Failed to fetch dynamic telemetry counts:", err);
    }
  }, []);

  useEffect(() => {
    refreshCounts();
    // Automatic live polling every 3.5 seconds
    const timer = setInterval(refreshCounts, 3500);
    return () => clearInterval(timer);
  }, [refreshCounts]);

  const [notifications, setNotifications] = useState([
    {
      id: 1,
      title: 'CRITICAL: Database connection exhaustion',
      server: 'Server-03',
      time: '2m ago',
      unread: true,
      severity: 'critical'
    },
    {
      id: 2,
      title: 'HIGH: Suspicious brute-force login attempts',
      server: 'Server-02',
      time: '12m ago',
      unread: true,
      severity: 'warning'
    },
    {
      id: 3,
      title: 'INFO: Automated daily log retention backup completed',
      server: 'CloudWatch',
      time: '1h ago',
      unread: false,
      severity: 'info'
    }
  ]);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 3500);
  };

  const navigateToIncident = (incidentId) => {
    setSelectedIncidentId(incidentId);
    setActiveTab('incidents');
  };

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        selectedIncidentId,
        setSelectedIncidentId,
        activeEnvironment,
        setActiveEnvironment,
        notifications,
        setNotifications,
        toast,
        showToast,
        navigateToIncident,
        counts,
        setCounts,
        refreshCounts,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
