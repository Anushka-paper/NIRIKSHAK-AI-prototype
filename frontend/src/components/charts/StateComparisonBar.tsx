"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { StateSummary } from "@/types/overview";

interface StateComparisonBarProps {
  data: StateSummary[];
  topN?: number;
  direction?: "top" | "bottom";
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as StateSummary;
  return (
    <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-4 py-3 text-sm">
      <p className="font-bold text-gray-900 mb-1">{label}</p>
      <p className="text-xs text-emerald-700 font-bold">{d.completionRate}% completion rate</p>
      <p className="text-xs text-gray-500 mt-0.5">{d.totalProjects.toLocaleString()} total works</p>
    </div>
  );
};

export default function StateComparisonBar({ data, topN = 10, direction = "top" }: StateComparisonBarProps) {
  const sorted = [...data]
    .sort((a, b) => direction === "top" ? b.completionRate - a.completionRate : a.completionRate - b.completionRate)
    .slice(0, topN)
    .map((d) => ({ ...d, name: d.name.length > 16 ? d.name.slice(0, 15) + "…" : d.name }));

  if (sorted.length === 0) return null;

  return (
    <div className="w-full" style={{ height: Math.max(240, sorted.length * 32) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={sorted}
          margin={{ top: 4, right: 40, left: 8, bottom: 4 }}
          barCategoryGap="26%"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="name"
            width={120}
            tick={{ fontSize: 11, fill: "#374151", fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "#fef9f0" }} />
          <Bar dataKey="completionRate" name="Completion Rate" radius={[0, 6, 6, 0]} maxBarSize={20}>
            {sorted.map((d, i) => (
              <Cell key={i} fill={d.completionRate >= 70 ? "#10b981" : d.completionRate >= 40 ? "#f59e0b" : "#ef4444"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
