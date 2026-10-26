import React from 'react';

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className = ''
}) {
  const getStyles = () => {
    const v = String(variant).toLowerCase();
    if (v === 'critical' || v === 'high risk' || v === 'error') {
      return 'bg-red-50 text-red-700 border-red-200/80';
    }
    if (v === 'high' || v === 'warning' || v === 'warn' || v === 'medium risk') {
      return 'bg-amber-50 text-amber-800 border-amber-200/80';
    }
    if (v === 'healthy' || v === 'resolved' || v === 'low risk' || v === 'success' || v === 'normal' || v === 'blocked') {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200/80';
    }
    if (v === 'info' || v === 'investigating' || v === 'open' || v === 'monitored' || v === 'generated') {
      return 'bg-blue-50 text-blue-700 border-blue-200/80';
    }
    if (v === 'medium') {
      return 'bg-slate-100 text-slate-800 border-slate-200';
    }
    return 'bg-slate-50 text-slate-700 border-slate-200';
  };

  const getDotColor = () => {
    const v = String(variant).toLowerCase();
    if (v === 'critical' || v === 'high risk' || v === 'error') return 'bg-red-500';
    if (v === 'high' || v === 'warning' || v === 'warn' || v === 'medium risk') return 'bg-amber-500';
    if (v === 'healthy' || v === 'resolved' || v === 'low risk' || v === 'success' || v === 'normal' || v === 'blocked') return 'bg-emerald-500';
    if (v === 'info' || v === 'investigating' || v === 'open' || v === 'monitored') return 'bg-blue-500';
    return 'bg-slate-400';
  };

  const sizes = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs font-medium px-2.5 py-1',
    lg: 'text-sm font-medium px-3 py-1',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border tracking-tight ${sizes[size]} ${getStyles()} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${getDotColor()}`} />}
      {children}
    </span>
  );
}
