import React from 'react';
import Card from '../common/Card';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

export default function ActivityChart({ data }) {
  return (
    <Card className="p-3.5 sm:p-4">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-xs sm:text-sm font-semibold text-slate-900">Log Activity Over Time</h3>
          <p className="text-[11px] text-slate-500">Hourly log ingestion rate (events/sec)</p>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2 h-2 rounded-full bg-blue-600 inline-block" />
          <span>Ingested Requests</span>
        </div>
      </div>

      <div className="h-44 sm:h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
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
              tickFormatter={(v) => `${v / 1000}k`}
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
            <Line
              type="monotone"
              dataKey="requests"
              stroke="#2563eb"
              strokeWidth={1.75}
              dot={{ r: 2.5, fill: '#2563eb' }}
              activeDot={{ r: 4, fill: '#1d4ed8' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
