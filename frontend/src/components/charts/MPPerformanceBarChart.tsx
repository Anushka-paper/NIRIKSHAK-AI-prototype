"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { MPPerformanceRecord } from "@/components/features/MPPerformanceSection";

interface MPPerformanceBarChartProps {
  data: MPPerformanceRecord[];
  metric: "works" | "rate" | "finance";
  topN?: number;
}

const fmtINR = (v: number) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${v.toLocaleString()}`;
};

const METRIC_CONFIG = {
  works: { dataKey: "total_works", color: "#f97316", label: "Total Works" },
  rate: { dataKey: "completion_rate", color: "#10b981", label: "Completion Rate (%)" },
  finance: { dataKey: "sanctioned_amount", color: "#0ea5e9", label: "Sanctioned Funds" },
} as const;

const CustomTooltip = ({ active, payload, label, metric }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as MPPerformanceRecord;
  return (
    <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-4 py-3 text-sm">
      <p className="font-bold text-gray-900 mb-1">{label}</p>
      {metric === "finance" ? (
        <p className="text-xs text-sky-700 font-bold">{fmtINR(d.sanctioned_amount)} sanctioned</p>
      ) : metric === "rate" ? (
        <p className="text-xs text-emerald-700 font-bold">{d.completion_rate}% completion rate</p>
      ) : (
        <p className="text-xs text-orange-700 font-bold">{d.total_works} total works ({d.completed_works} completed)</p>
      )}
    </div>
  );
};

export default function MPPerformanceBarChart({ data, metric, topN = 10 }: MPPerformanceBarChartProps) {
  const cfg = METRIC_CONFIG[metric];
  const sorted = [...data]
    .sort((a, b) => (b as any)[cfg.dataKey] - (a as any)[cfg.dataKey])
    .slice(0, topN)
    .map((d) => ({ ...d, mp_name: d.mp_name.length > 16 ? d.mp_name.slice(0, 15) + "…" : d.mp_name }));

  if (sorted.length === 0) return null;

  return (
    <div className="w-full" style={{ height: Math.max(240, sorted.length * 34) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={sorted}
          margin={{ top: 4, right: 40, left: 8, bottom: 4 }}
          barCategoryGap="28%"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 10, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="mp_name"
            width={120}
            tick={{ fontSize: 11, fill: "#374151", fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip metric={metric} />} cursor={{ fill: "#fef9f0" }} />
          <Bar dataKey={cfg.dataKey} name={cfg.label} radius={[0, 6, 6, 0]} maxBarSize={22}>
            {sorted.map((_, i) => (
              <Cell key={i} fill={cfg.color} fillOpacity={1 - i * 0.06} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
