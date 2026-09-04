"use client";

import React, { useState } from "react";
import { 
  BarChart3, 
  TrendingUp, 
  PieChart as PieIcon, 
  AlertTriangle, 
  Sparkles, 
  Layers, 
  Activity,
  ArrowUpRight
} from "lucide-react";

interface StateBreakdown {
  state: string;
  anomaly_count: number;
  at_risk_amount: number;
}

interface RiskBand {
  band: string;
  count: number;
  color: string;
}

interface ReasonBreakdown {
  reason: string;
  count: number;
}

interface ScatterPoint {
  work_id: string;
  state: string;
  cost_lakhs: number;
  score: number;
  deviation: number;
  reasons: string;
}

interface VisualGraphsProps {
  stateBreakdown: StateBreakdown[];
  riskBands: RiskBand[];
  reasonBreakdown: ReasonBreakdown[];
  scatterPoints: ScatterPoint[];
  formatCurrency: (val: number) => string;
}

export default function VisualGraphs({
  stateBreakdown,
  riskBands,
  reasonBreakdown,
  scatterPoints,
  formatCurrency
}: VisualGraphsProps) {
  const [hoveredPoint, setHoveredPoint] = useState<ScatterPoint | null>(null);

  const maxStateCount = stateBreakdown?.[0]?.anomaly_count || 1;
  const maxReasonCount = reasonBreakdown?.[0]?.count || 1;
  const totalBands = riskBands?.reduce((acc, b) => acc + b.count, 0) || 1;

  // Donut Chart Math
  let cumulativeAngle = 0;
  const donutSlices = riskBands.map(band => {
    const fraction = band.count / totalBands;
    const angle = fraction * 360;
    const startAngle = cumulativeAngle;
    const endAngle = cumulativeAngle + angle;
    cumulativeAngle += angle;

    const startRad = (startAngle - 90) * (Math.PI / 180);
    const endRad = (endAngle - 90) * (Math.PI / 180);

    const x1 = 100 + 75 * Math.cos(startRad);
    const y1 = 100 + 75 * Math.sin(startRad);
    const x2 = 100 + 75 * Math.cos(endRad);
    const y2 = 100 + 75 * Math.sin(endRad);

    const largeArcFlag = angle > 180 ? 1 : 0;
    const pathData = `M 100 100 L ${x1} ${y1} A 75 75 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;

    return {
      band: band.band,
      count: band.count,
      pct: Math.round(fraction * 100),
      color: band.color,
      pathData
    };
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Top Grid: Interactive Donut & Scatter Plot */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Visual 1: SVG Donut Chart */}
        <div className="lg:col-span-4 bg-white rounded-3xl p-6 border border-gray-100 shadow-subtle flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <h3 className="font-headline font-bold text-base text-gray-900 flex items-center gap-2">
                <PieIcon className="w-4 h-4 text-amber-500" /> Risk Band Proportions
              </h3>
              <span className="text-[11px] font-bold text-gray-400 uppercase">Donut View</span>
            </div>
            <p className="text-xs text-gray-500 mb-6">Proportion of projects by risk severity level</p>

            {/* SVG Donut */}
            <div className="relative flex items-center justify-center my-4">
              <svg width="200" height="200" viewBox="0 0 200 200" className="transform -rotate-90">
                {donutSlices.map((s, i) => (
                  <path
                    key={s.band}
                    d={s.pathData}
                    fill={s.color}
                    className="hover:opacity-85 transition-opacity cursor-pointer"
                  />
                ))}
                {/* Center Hole for Donut Effect */}
                <circle cx="100" cy="100" r="50" fill="white" />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
                <span className="text-xl font-headline font-extrabold text-gray-900">
                  {totalBands.toLocaleString()}
                </span>
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">Works</span>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="grid grid-cols-2 gap-2.5 mt-4 pt-4 border-t border-gray-100">
            {donutSlices.map(s => (
              <div key={s.band} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
                <div className="flex flex-col">
                  <span className="text-[11px] font-bold text-gray-800 leading-none">{s.band.split(" ")[0]}</span>
                  <span className="text-[10px] text-gray-400 font-mono mt-0.5">{s.count.toLocaleString()} ({s.pct}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Visual 2: Coordinate Scatter Graph (Cost Deviation vs Anomaly Risk Score) */}
        <div className="lg:col-span-8 bg-white rounded-3xl p-6 border border-gray-100 shadow-subtle flex flex-col justify-between relative">
          <div>
            <div className="flex items-center justify-between mb-1">
              <h3 className="font-headline font-bold text-base text-gray-900 flex items-center gap-2">
                <Activity className="w-4 h-4 text-rose-600" /> Multivariate Outlier Landscape
              </h3>
              <span className="text-[11px] font-bold text-gray-400 uppercase">Interactive Scatter</span>
            </div>
            <p className="text-xs text-gray-500 mb-4">
              X-Axis: Cost Deviation % from District Median &bull; Y-Axis: Isolation Forest Risk Score %
            </p>

            {/* SVG Scatter Plot Canvas */}
            <div className="relative w-full h-64 bg-gray-50/60 rounded-2xl border border-gray-100 p-4 flex flex-col justify-between overflow-hidden">
              {/* Grid Lines */}
              <div className="absolute inset-0 grid grid-rows-4 grid-cols-4 pointer-events-none opacity-30">
                <div className="border-b border-r border-gray-300" />
                <div className="border-b border-r border-gray-300" />
                <div className="border-b border-r border-gray-300" />
                <div className="border-b border-gray-300" />
                <div className="border-b border-r border-gray-300" />
                <div className="border-b border-r border-gray-300" />
                <div className="border-b border-r border-gray-300" />
                <div className="border-b border-gray-300" />
                <div className="border-b border-r border-gray-300" />
                <div className="border-b border-r border-gray-300" />
                <div className="border-b border-r border-gray-300" />
                <div className="border-b border-gray-300" />
              </div>

              {/* Points */}
              <svg className="w-full h-full relative z-10" viewBox="0 0 500 220">
                {/* Axes Labels in SVG */}
                <line x1="40" y1="200" x2="480" y2="200" stroke="#CBD5E1" strokeWidth="1.5" />
                <line x1="40" y1="20" x2="40" y2="200" stroke="#CBD5E1" strokeWidth="1.5" />

                <text x="45" y="30" fontSize="9" fill="#94A3B8" fontWeight="bold">100% Risk</text>
                <text x="45" y="110" fontSize="9" fill="#94A3B8" fontWeight="bold">75% Risk</text>
                <text x="45" y="195" fontSize="9" fill="#94A3B8" fontWeight="bold">50% Risk</text>
                <text x="440" y="195" fontSize="9" fill="#94A3B8" fontWeight="bold">+1500% Cost</text>

                {scatterPoints.map((pt, i) => {
                  // Map deviation [0, 1500] -> X [50, 470]
                  const clampDev = Math.max(0, Math.min(1500, pt.deviation));
                  const cx = 50 + (clampDev / 1500) * 410;
                  // Map score [50, 100] -> Y [190, 30]
                  const clampScore = Math.max(50, Math.min(100, pt.score));
                  const cy = 190 - ((clampScore - 50) / 50) * 160;

                  const isHigh = pt.score >= 85;

                  return (
                    <circle
                      key={`${pt.work_id}-${i}`}
                      cx={cx}
                      cy={cy}
                      r={isHigh ? 5.5 : 4}
                      fill={isHigh ? "#EF4444" : "#F59E0B"}
                      className="cursor-pointer transition-all hover:scale-150 hover:stroke-white hover:stroke-2"
                      onMouseEnter={() => setHoveredPoint(pt)}
                      onMouseLeave={() => setHoveredPoint(null)}
                    />
                  );
                })}
              </svg>

              {/* Tooltip Card */}
              {hoveredPoint && (
                <div className="absolute top-3 right-3 bg-gray-900/95 text-white p-3 rounded-xl shadow-xl z-20 max-w-xs pointer-events-none text-xs backdrop-blur">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="font-bold text-amber-400">{hoveredPoint.state}</span>
                    <span className="font-mono bg-rose-500/20 text-rose-300 px-1.5 py-0.5 rounded text-[10px]">
                      {hoveredPoint.score}% Risk
                    </span>
                  </div>
                  <p className="text-gray-200 line-clamp-1 font-medium">{hoveredPoint.work_id}</p>
                  <div className="flex items-center gap-3 mt-1.5 text-[11px] text-gray-400">
                    <span>Dev: +{hoveredPoint.deviation}%</span>
                    <span>Cost: {hoveredPoint.cost_lakhs > 0 ? `₹${hoveredPoint.cost_lakhs}L` : "N/A"}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-gray-400 font-medium px-2 pt-3 border-t border-gray-100">
            <span>🔴 Critical Risk (&ge;85% outlier)</span>
            <span>🟡 High Risk (70-84% outlier)</span>
            <span>Hover any point to inspect work details</span>
          </div>
        </div>
      </div>

      {/* Bottom Grid: Visual Bar Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Visual 3: State Bar Chart with Financials */}
        <div className="lg:col-span-7 bg-white rounded-3xl p-6 border border-gray-100 shadow-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-headline font-bold text-base text-gray-900 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" /> State-wise Anomaly Volume & At-Risk Capital
              </h3>
              <p className="text-xs text-gray-500">Ranked by count of irregular works flagged by Isolation Forest</p>
            </div>
            <span className="text-[11px] font-bold text-gray-400 uppercase">Top 10 States</span>
          </div>

          <div className="flex flex-col gap-3">
            {stateBreakdown.map((s, i) => {
              const widthPct = Math.max(8, Math.round((s.anomaly_count / maxStateCount) * 100));
              return (
                <div key={s.state} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between text-xs font-bold text-gray-700">
                    <span className="flex items-center gap-1.5">
                      <span className="w-4 text-gray-400 font-mono text-[10px]">{i + 1}</span>
                      {s.state}
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="text-rose-600">{s.anomaly_count.toLocaleString()} works</span>
                      <span className="text-gray-400 text-[11px] font-mono">({formatCurrency(s.at_risk_amount)})</span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-rose-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Visual 4: Root Causes Ranking */}
        <div className="lg:col-span-5 bg-white rounded-3xl p-6 border border-gray-100 shadow-subtle flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-headline font-bold text-base text-gray-900 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-500" /> Irregularity Root Causes
              </h3>
              <span className="text-[11px] font-bold text-gray-400 uppercase">Frequency</span>
            </div>
            <p className="text-xs text-gray-500 mb-4">Core reasons identified across flagged works</p>

            <div className="flex flex-col gap-3.5">
              {reasonBreakdown.map(reason => {
                const widthPct = Math.max(10, Math.round((reason.count / maxReasonCount) * 100));
                return (
                  <div key={reason.reason} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-xs font-medium">
                      <span className="text-gray-700 truncate max-w-[200px]">{reason.reason}</span>
                      <span className="font-bold text-gray-900">{reason.count.toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-primary h-full rounded-full transition-all duration-500"
                        style={{ width: `${widthPct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-4 p-3 bg-primary/5 rounded-xl border border-primary/10 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary shrink-0" />
            <span className="text-[11px] text-primary font-bold">
              Multi-factor anomalies flag when multiple root causes co-occur on a single work.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
