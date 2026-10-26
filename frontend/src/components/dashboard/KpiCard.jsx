import React from 'react';
import Card from '../common/Card';

export default function KpiCard({ title, value, subtitle, status = 'default', icon: Icon }) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-emerald-600 bg-emerald-50 border-emerald-100';
      case 'warning':
        return 'text-amber-600 bg-amber-50 border-amber-100';
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-100';
      case 'info':
        return 'text-blue-600 bg-blue-50 border-blue-100';
      default:
        return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  return (
    <Card className="p-3 sm:p-3.5">
      <div className="flex items-center justify-between gap-1 mb-1.5">
        <span className="text-[11px] font-medium text-slate-500 truncate">{title}</span>
        {Icon && (
          <div className={`p-1.5 rounded-md border shrink-0 ${getStatusColor()}`}>
            <Icon className="w-3.5 h-3.5" />
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-xl font-bold text-slate-900 tracking-tight">{value}</span>
      </div>
      {subtitle && (
        <p className="mt-0.5 text-[11px] text-slate-400 font-normal truncate">{subtitle}</p>
      )}
    </Card>
  );
}
