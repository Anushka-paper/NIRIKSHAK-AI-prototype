"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export interface MonthlyTrendItem {
  month: string;
  compliant: number;
  under_review: number;
  non_compliant: number;
}

interface ComplianceTrendLineProps {
  data: MonthlyTrendItem[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-4 py-3 text-sm">
      <p className="font-bold text-gray-900 mb-1.5">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} className="text-xs" style={{ color: p.color }}>
          <span className="font-bold">{p.value.toLocaleString()}</span> {p.name}
        </p>
      ))}
    </div>
  );
};

export default function ComplianceTrendLine({ data }: ComplianceTrendLineProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-xs text-gray-400 font-semibold">
        No trend data available yet.
      </div>
    );
  }

  return (
    <div className="w-full" style={{ height: 220 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
          <XAxis dataKey="month" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Line type="monotone" dataKey="compliant" name="Compliant" stroke="#10b981" strokeWidth={2.5} dot={{ r: 3.5 }} />
          <Line type="monotone" dataKey="under_review" name="Under Review" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 3.5 }} />
          <Line type="monotone" dataKey="non_compliant" name="Non-Compliant" stroke="#ef4444" strokeWidth={2.5} dot={{ r: 3.5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
