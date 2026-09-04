"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface StateBreakdown {
  state: string;
  anomaly_count: number;
  at_risk_amount?: number;
}

interface StateHeatBarProps {
  data: StateBreakdown[];
  topN?: number;
}

const fmt = (v: number) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000)   return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${v.toLocaleString()}`;
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as StateBreakdown;
  return (
    <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-4 py-3 text-sm">
      <p className="font-bold text-gray-900 mb-1">{label}</p>
      <p className="text-xs text-red-600 font-bold">{d.anomaly_count} anomalies detected</p>
      {d.at_risk_amount != null && d.at_risk_amount > 0 && (
        <p className="text-xs text-amber-600 font-medium mt-0.5">At-risk: {fmt(d.at_risk_amount)}</p>
      )}
    </div>
  );
};

// Color scale from amber → red based on rank
const BAR_COLORS = [
  "#dc2626","#ef4444","#f87171","#fb923c","#fbbf24",
  "#fcd34d","#fde68a","#fef3c7","#ecfccb","#d1fae5",
];

export default function StateHeatBar({ data, topN = 10 }: StateHeatBarProps) {
  const sorted = [...data]
    .sort((a, b) => b.anomaly_count - a.anomaly_count)
    .slice(0, topN)
    .map((d) => ({ ...d, state: d.state.length > 14 ? d.state.slice(0, 13) + "…" : d.state }));

  return (
    <div className="w-full" style={{ height: Math.max(260, sorted.length * 36) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={sorted}
          margin={{ top: 4, right: 40, left: 8, bottom: 4 }}
          barCategoryGap="30%"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="state"
            width={110}
            tick={{ fontSize: 11, fill: "#374151", fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "#fef9f0" }} />
          <Bar dataKey="anomaly_count" name="Anomalies" radius={[0, 6, 6, 0]} maxBarSize={24}>
            {sorted.map((_, i) => (
              <Cell key={i} fill={BAR_COLORS[Math.min(i, BAR_COLORS.length - 1)]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
