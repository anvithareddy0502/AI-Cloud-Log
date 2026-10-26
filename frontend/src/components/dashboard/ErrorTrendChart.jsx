import React from 'react';
import Card from '../common/Card';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

export default function ErrorTrendChart({ data }) {
  return (
    <Card className="p-3.5 sm:p-4">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-xs sm:text-sm font-semibold text-slate-900">Error Trend</h3>
          <p className="text-[11px] text-slate-500">Error distribution across recent time windows</p>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
          <span>Error Count</span>
        </div>
      </div>

      <div className="h-44 sm:h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="#94a3b8"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={10}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                borderColor: '#e2e8f0',
                borderRadius: '6px',
                fontSize: '11px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.06)'
              }}
            />
            <Bar
              dataKey="errors"
              fill="#ef4444"
              radius={[3, 3, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
