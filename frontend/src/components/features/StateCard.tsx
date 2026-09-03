"use client";

import React from "react";
import Link from "next/link";
import { StateSummary } from "@/types/overview";
import { ArrowRight, CheckCircle2, Clock, AlertCircle, IndianRupee } from "lucide-react";

interface StateCardProps {
  state: StateSummary;
  parliament?: string;
}

export default function StateCard({ state, parliament = "all" }: StateCardProps) {
  const formatINR = (val?: number) => {
    if (!val || isNaN(val)) return "₹0";
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    return `₹${val.toLocaleString()}`;
  };

  return (
    <Link
      href={`/overview/state/${state.id}?parliament=${parliament}`}
      className="group bg-white rounded-2xl p-5 border border-gray-100 shadow-subtle hover:shadow-medium hover:border-primary/30 transition-all duration-200 flex flex-col justify-between flex-1 min-w-[280px]"
    >
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="font-headline font-bold text-lg text-gray-900 group-hover:text-primary transition-colors">
            {state.name}
          </span>
          <span
            className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full ${
              state.type === "UT"
                ? "bg-purple-100 text-purple-700"
                : "bg-blue-100 text-blue-700"
            }`}
          >
            {state.type}
          </span>
        </div>

        {/* High-level metrics */}
        <div className="grid grid-cols-2 gap-2 pb-3 mb-3 border-b border-gray-100">
          <div>
            <span className="text-[10px] uppercase font-bold text-gray-400 block">Total Works</span>
            <span className="font-headline font-bold text-xl text-gray-900 block mt-0.5">
              {state.totalProjects.toLocaleString()}
            </span>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-gray-400 block">Sanctioned</span>
            <span className="font-headline font-bold text-lg text-primary block mt-0.5">
              {formatINR(state.sanctionedAmount)}
            </span>
          </div>
        </div>

        {/* Status breakdown */}
        <div className="space-y-1.5 text-xs">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-gray-600">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Completed</span>
            </span>
            <span className="font-bold text-emerald-700 font-mono">
              {state.completedProjects.toLocaleString()} ({state.completionRate}%)
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-gray-600">
              <Clock className="w-3.5 h-3.5 text-primary" />
              <span>Ongoing</span>
            </span>
            <span className="font-bold text-primary font-mono">
              {state.ongoingProjects.toLocaleString()}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-gray-600">
              <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
              <span>Pending</span>
            </span>
            <span className="font-bold text-amber-700 font-mono">
              {state.pendingProjects.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Card Action Link */}
      <div className="pt-4 border-t border-gray-100 mt-4 flex items-center justify-between">
        <span className="text-[11px] text-gray-500 font-medium">
          Expenditure: <strong className="text-secondary">{formatINR(state.expenditureAmount)}</strong>
        </span>
        <span className="text-xs font-bold text-primary flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
          Open <ArrowRight className="w-3.5 h-3.5" />
        </span>
      </div>
    </Link>
  );
}
