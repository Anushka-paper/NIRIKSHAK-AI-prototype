"use client";

import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface StatusDonutProps {
  completed: number;
  ongoing: number;
  pending: number;
}

const ITEMS = [
  { key: "completed", label: "Completed", color: "#10b981" },
  { key: "ongoing",   label: "Ongoing",   color: "#6366f1" },
  { key: "pending",   label: "Pending",   color: "#f59e0b" },
];

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-4 py-2.5 text-sm">
      <span className="font-bold text-gray-900">{d.name}</span>
      <p className="text-gray-600 mt-0.5">{d.value.toLocaleString()} projects</p>
      <p className="text-xs text-gray-400">{d.payload.pct}% of total</p>
    </div>
  );
};

const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, pct }: any) => {
  if (pct < 5) return null;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.55;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central"
      style={{ fontSize: 11, fontWeight: 700 }}>
      {pct}%
    </text>
  );
};

export default function StatusDonut({ completed, ongoing, pending }: StatusDonutProps) {
  const total = completed + ongoing + pending || 1;
  const data = ITEMS.map(({ key, label, color }) => {
    const value = key === "completed" ? completed : key === "ongoing" ? ongoing : pending;
    return { name: label, value, color, pct: Math.round((value / total) * 100) };
  });

  return (
    <div className="w-full" style={{ height: 280 }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="45%"
            innerRadius={72}
            outerRadius={108}
            paddingAngle={3}
            dataKey="value"
            labelLine={false}
            label={renderCustomLabel}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} stroke="white" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(value) => (
              <span style={{ fontSize: 12, fontWeight: 600, color: "#374151" }}>{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
