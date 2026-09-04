"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine
} from "recharts";

interface OverviewFinancialProps {
  allocated: number;
  sanctioned: number;
  expenditure: number;
  calamity?: number;
}

const fmt = (v: number) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000)   return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${v.toLocaleString()}`;
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-4 py-3 text-sm">
      <p className="font-bold text-gray-900 mb-1">{label}</p>
      <p className="text-xs text-gray-500">Amount: <span className="font-bold text-gray-900">{fmt(payload[0]?.value)}</span></p>
    </div>
  );
};

const BARS = [
  { key: "Allocated",    color: "#818cf8" },
  { key: "Sanctioned",   color: "#6366f1" },
  { key: "Expenditure",  color: "#10b981" },
  { key: "Calamity",     color: "#f59e0b" },
];

export default function OverviewFinancial({ allocated, sanctioned, expenditure, calamity = 0 }: OverviewFinancialProps) {
  const data = [
    { name: "Allocated",   value: allocated },
    { name: "Sanctioned",  value: sanctioned },
    { name: "Expenditure", value: expenditure },
    { name: "Calamity",    value: calamity },
  ];

  return (
    <div className="w-full" style={{ height: 240 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 20, left: 30, bottom: 5 }} barCategoryGap="35%">
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: "#6b7280", fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={fmt}
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f8fafc" }} />
          <Bar dataKey="value" radius={[8, 8, 0, 0]} maxBarSize={70}>
            {data.map((_, i) => (
              <Cell key={i} fill={BARS[i % BARS.length].color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
