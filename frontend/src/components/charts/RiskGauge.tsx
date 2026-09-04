"use client";

import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface RiskGaugeProps {
  probability: number; // 0.0 – 1.0
  riskLevel: "LOW" | "MEDIUM" | "HIGH" | string;
  delayDays?: number;
}

const COLORS = {
  HIGH: { bar: "#ef4444", bg: "#fef2f2", text: "#b91c1c", label: "bg-red-100 text-red-700" },
  MEDIUM: { bar: "#f59e0b", bg: "#fffbeb", text: "#92400e", label: "bg-amber-100 text-amber-800" },
  LOW: { bar: "#10b981", bg: "#ecfdf5", text: "#065f46", label: "bg-emerald-100 text-emerald-700" },
};

export default function RiskGauge({ probability, riskLevel, delayDays }: RiskGaugeProps) {
  const pct = Math.round(Math.min(1, Math.max(0, probability)) * 100);
  const tier = riskLevel?.toUpperCase() as keyof typeof COLORS;
  const col = COLORS[tier] ?? COLORS["MEDIUM"];

  const data = [{ value: pct, fill: col.bar }];

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: 200, height: 115 }}>
        <RadialBarChart
          width={200}
          height={130}
          cx={100}
          cy={115}
          startAngle={180}
          endAngle={0}
          innerRadius={72}
          outerRadius={96}
          barSize={18}
          data={data}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar
            background={{ fill: "#f1f5f9" }}
            dataKey="value"
            angleAxisId={0}
            cornerRadius={6}
          />
        </RadialBarChart>

        {/* Center overlay text */}
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-3 pointer-events-none">
          <span className="font-headline font-extrabold text-3xl" style={{ color: col.text }}>
            {pct}%
          </span>
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest -mt-1">
            Risk Score
          </span>
        </div>
      </div>

      <span
        className={`text-xs font-extrabold uppercase tracking-wider px-3 py-1 rounded-full ${col.label}`}
      >
        {riskLevel} RISK
      </span>

      {delayDays !== undefined && (
        <span className="text-[11px] text-gray-500 font-medium">
          Predicted delay:{" "}
          <strong className="text-gray-800">
            {delayDays > 0 ? `+${delayDays} days` : "On Track"}
          </strong>
        </span>
      )}
    </div>
  );
}
