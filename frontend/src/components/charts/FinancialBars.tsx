"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Cell
} from "recharts";

interface FinancialBarsProps {
  recommended: number;
  sanctioned: number;
  spent: number;
  label?: string;
}

const fmt = (v: number) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000)   return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${v.toLocaleString()}`;
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-4 py-3 text-sm min-w-[160px]">
      <p className="font-bold text-gray-700 mb-2">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2 text-xs mb-1">
          <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: p.fill }} />
          <span className="text-gray-500">{p.name}:</span>
          <span className="font-bold text-gray-900">{fmt(p.value)}</span>
        </div>
      ))}
    </div>
  );
};

export default function FinancialBars({ recommended, sanctioned, spent, label }: FinancialBarsProps) {
  const data = [
    {
      name: label || "Budget Flow",
      Recommended: recommended,
      Sanctioned: sanctioned,
      Spent: spent,
    },
  ];

  const BAR_COLORS = ["#818cf8", "#6366f1", "#10b981"];

  return (
    <div className="w-full" style={{ height: 220 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 20, left: 20, bottom: 5 }} barCategoryGap="40%">
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
          <XAxis dataKey="name" tick={false} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={fmt} tick={{ fontSize: 10, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f8fafc" }} />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(v) => <span style={{ fontSize: 12, fontWeight: 600, color: "#374151" }}>{v}</span>}
          />
          {(["Recommended", "Sanctioned", "Spent"] as const).map((key, i) => (
            <Bar key={key} dataKey={key} fill={BAR_COLORS[i]} radius={[6, 6, 0, 0]} maxBarSize={60} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
