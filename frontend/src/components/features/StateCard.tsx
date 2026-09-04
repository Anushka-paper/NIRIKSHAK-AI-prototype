"use client";

import React, { useState } from "react";
import Link from "next/link";
import { StateSummary } from "@/types/overview";
import { Users, Info, MapPin, TrendingUp, CheckCircle2, ArrowRight } from "lucide-react";

interface StateCardProps {
  state: StateSummary;
  parliament?: string;
  className?: string;
}

export default function StateCard({ state, parliament = "all", className = "" }: StateCardProps) {
  const [showInfo, setShowInfo] = useState<boolean>(false);

  // Currency Formatter in Crores
  const formatCrores = (val?: number) => {
    if (!val || isNaN(val) || val <= 0) return "0.0 CR";
    const cr = val / 10000000;
    return `${cr.toFixed(1)} CR`;
  };

  // Dynamic values extracted directly from dataset / API
  const stateName = state.name || "State";
  const slug = state.id || state.name?.toLowerCase().replace(/\s+/g, "-");
  const mpCount = state.mpCount ?? 1;
  const rank = state.rank ?? 1;
  const totalStates = state.totalStates ?? 36;
  
  // Financial numbers
  const allocated = state.allocated ?? state.sanctionedAmount ?? 0;
  const recordedExpenditure = state.recordedExpenditure ?? state.expenditureAmount ?? 0;

  // Expenditure Rate Calculation
  const calculatedExpenditureRate =
    state.expenditureRate !== undefined && state.expenditureRate !== null
      ? state.expenditureRate
      : allocated > 0
      ? Number(((recordedExpenditure / allocated) * 100).toFixed(1))
      : 0;

  // Dynamic progress bar width clamped strictly between 0 and 100
  const progressWidth = Math.min(Math.max(calculatedExpenditureRate, 0), 100);

  // Works Completed & Completion Rate
  const worksCompleted = state.worksCompleted ?? state.completedProjects ?? 0;
  const completionRate = state.completionRate !== undefined && state.completionRate !== null
    ? state.completionRate
    : state.totalProjects > 0
    ? Number(((worksCompleted / state.totalProjects) * 100).toFixed(1))
    : 0;

  // Dynamic destination route
  const targetUrl = `/states/${slug}${parliament && parliament !== "all" ? `?parliament=${parliament}` : ""}`;

  return (
    <div
      className={`relative bg-white rounded-2xl p-5 sm:p-6 border border-gray-100 shadow-[0_2px_12px_rgba(0,0,0,0.04)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.07)] transition-all duration-200 w-full flex flex-col justify-between ${className}`}
      role="region"
      aria-label={`Performance overview for ${stateName}`}
    >
      <div>
        {/* ─── 1. HEADER SECTION ────────────────────────────────────────── */}
        <div className="flex items-start justify-between gap-3">
          {/* LEFT: State Name, MP count, Info Icon */}
          <div className="flex-1 min-w-0">
            <h3
              className="text-xl sm:text-2xl font-bold text-[#0F172A] leading-tight tracking-tight font-serif truncate"
              title={stateName}
            >
              {stateName}
            </h3>

            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              {/* MP Count with People Icon */}
              <div className="flex items-center gap-1 text-[#64748B] text-xs font-medium">
                <Users className="w-3.5 h-3.5 text-[#64748B]" aria-hidden="true" />
                <span>{mpCount} {mpCount === 1 ? "MP" : "MPs"}</span>
              </div>

              {/* Circular Blue Info Button */}
              <div className="relative inline-block">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowInfo((prev) => !prev);
                  }}
                  className="w-5 h-5 rounded-full bg-[#2563EB] hover:bg-[#1D4ED8] text-white flex items-center justify-center shadow-xs hover:scale-105 active:scale-95 transition-all focus:outline-none focus:ring-1 focus:ring-[#2563EB]/40"
                  aria-label={`More information about ${stateName}`}
                  title="View State Information"
                >
                  <Info className="w-3 h-3" />
                </button>

                {/* Popover / Tooltip */}
                {showInfo && (
                  <div
                    className="absolute left-0 top-7 z-30 w-56 p-3 bg-[#0F172A] text-white text-[11px] rounded-xl shadow-xl space-y-1 border border-slate-700 animate-in fade-in zoom-in-95 duration-150"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="font-bold text-slate-100 flex items-center justify-between">
                      <span>{stateName} Details</span>
                      <span className="text-[10px] text-emerald-400 font-mono">Rank #{rank}</span>
                    </div>
                    <p className="text-slate-300 leading-snug">
                      Total Projects: <strong className="text-white">{state.totalProjects.toLocaleString()}</strong>
                    </p>
                    <p className="text-slate-300 leading-snug">
                      Type: <strong className="text-white">{state.type === "UT" ? "Union Territory" : "Full State"}</strong>
                    </p>
                    <p className="text-slate-400 text-[9px] pt-1 border-t border-slate-700">
                      Source: Official MoSPI Portals
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* RIGHT: Ranking Pill + Location Icon Box */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Rank Badge */}
            <div className="bg-[#EFF6FF] text-[#1E40AF] px-2.5 py-1 rounded-full text-[11px] font-bold tracking-tight border border-[#DBEAFE]">
              Rank #{rank} of {totalStates}
            </div>

            {/* Location / Map Pin Icon Button */}
            <Link
              href={targetUrl}
              className="w-10 h-10 sm:w-11 sm:h-11 bg-[#E0F2FE] hover:bg-[#BAE6FD] text-[#0369A1] rounded-xl flex items-center justify-center transition-all duration-150 hover:scale-105 active:scale-95"
              aria-label={`Open map and detailed view for ${stateName}`}
              title={`View ${stateName} details`}
            >
              <MapPin className="w-5 h-5 stroke-[1.75]" />
            </Link>
          </div>
        </div>

        {/* ─── 2. SUBTLE HORIZONTAL DIVIDER ──────────────────────────────── */}
        <div className="w-full h-px bg-gray-100 my-4" />

        {/* ─── 3. FINANCIAL METRICS (TWO-COLUMN) ─────────────────────────── */}
        <div className="grid grid-cols-2 gap-3 sm:gap-4">
          {/* Column 1: Allocated */}
          <div>
            <span className="text-[#64748B] text-xs font-medium block">
              Allocated
            </span>
            <span className="text-[#0F172A] text-lg sm:text-xl font-bold tracking-tight block mt-0.5 font-mono">
              {formatCrores(allocated)}
            </span>
          </div>

          {/* Column 2: Recorded Expenditure */}
          <div>
            <span className="text-[#64748B] text-xs font-medium block">
              Recorded expenditure
            </span>
            <span className="text-[#0F172A] text-lg sm:text-xl font-bold tracking-tight block mt-0.5 font-mono">
              {formatCrores(recordedExpenditure)}
            </span>
          </div>
        </div>

        {/* ─── 4. EXPENDITURE RATE & PROGRESS BAR ────────────────────────── */}
        <div className="mt-4 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[#1E293B] text-xs sm:text-sm font-semibold">
              Expenditure Rate
            </span>
            <div className="flex items-center gap-1 text-xs sm:text-sm font-bold text-[#16A34A]">
              <TrendingUp className="w-3.5 h-3.5 text-[#16A34A] stroke-[2.5]" aria-hidden="true" />
              <span className="font-mono">{calculatedExpenditureRate.toFixed(1)}%</span>
            </div>
          </div>

          {/* Dynamic Horizontal Progress Bar */}
          <div
            className="w-full h-2 sm:h-2.5 bg-[#F1F5F9] rounded-full overflow-hidden"
            role="progressbar"
            aria-valuenow={calculatedExpenditureRate}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Expenditure rate is ${calculatedExpenditureRate}%`}
          >
            <div
              className="h-full bg-[#16A34A] rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progressWidth}%` }}
            />
          </div>
        </div>

        {/* ─── 5. COMPLETION / WORKS COMPLETED SECTION ────────────────────── */}
        <div className="mt-4 flex items-center justify-between">
          {/* LEFT: Green circular check + Number + Works Completed */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full border border-[#16A34A] flex items-center justify-center text-[#16A34A] shrink-0">
              <CheckCircle2 className="w-4 h-4 stroke-[2]" aria-hidden="true" />
            </div>
            <div>
              <span className="text-[#0F172A] text-base sm:text-lg font-bold leading-none block font-mono">
                {worksCompleted.toLocaleString()}
              </span>
              <span className="text-[#64748B] text-[11px] font-medium block mt-0.5">
                Works Completed
              </span>
            </div>
          </div>

          {/* RIGHT: Completion Label + Completion Percentage */}
          <div className="text-right">
            <span className="text-[#64748B] text-[11px] font-medium block">
              Completion
            </span>
            <span className="text-[#1E3A8A] text-base sm:text-lg font-bold leading-none block mt-0.5 font-mono">
              {completionRate.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      <div>
        {/* ─── 6. SECOND DIVIDER ─────────────────────────────────────────── */}
        <div className="w-full h-px bg-gray-100 my-4" />

        {/* ─── 7. VIEW DETAILS ACTION (BOTTOM CENTER) ────────────────────── */}
        <div className="text-center">
          <Link
            href={targetUrl}
            className="group inline-flex items-center justify-center gap-1.5 text-[#2563EB] hover:text-[#1D4ED8] text-xs sm:text-sm font-semibold transition-colors focus:outline-none focus:underline"
          >
            <span>View Details</span>
            <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </div>
    </div>
  );
}
