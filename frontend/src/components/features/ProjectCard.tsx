"use client";

import React from "react";
import Link from "next/link";
import { WorkFeature } from "@/types/features";
import { 
  IndianRupee, 
  MapPin, 
  Calendar, 
  Clock, 
  Eye, 
  ExternalLink,
  ShieldCheck, 
  User, 
  Layers
} from "lucide-react";

interface ProjectCardProps {
  work: WorkFeature;
  onViewDetails: (work: WorkFeature) => void;
}

export default function ProjectCard({ work, onViewDetails }: ProjectCardProps) {
  const formatCurrency = (val?: number) => {
    if (!val || isNaN(val)) return "₹0";
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    return `₹${val.toLocaleString()}`;
  };

  const utilizationPct = Math.min(
    150, 
    Math.max(0, Math.round(((work.expenditure_to_sanction_ratio || 0) * 100)))
  );
  const isOverBudget = (work.expenditure_to_sanction_ratio || 0) > 1.0;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "EXPENDITURE_STARTED":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "SANCTIONED":
        return "bg-amber-50 text-amber-700 border-amber-200";
      default:
        return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  // Derived ML Model Risk Badge from engineered features
  // Derived ML Model Risk Badge from actual model output
  const riskTier = work.risk_level || "LOW";
  const anomalyScore = work.anomaly_score ? (Number(work.anomaly_score) * 100).toFixed(0) : null;

  // Normalize casing for constituency (raw CSV is all-caps)
  const displayConstituency = work.constituency
    ? work.constituency
        .split(" ")
        .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
        .join(" ")
    : "";

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-subtle hover:shadow-medium hover:-translate-y-1 transition-all duration-200 flex flex-col justify-between group">
      {/* Top Header */}
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg bg-primary/10 text-primary border border-primary/20">
              {work.canonical_work_id}
            </span>
            <span className="text-[11px] uppercase font-bold px-2 py-0.5 rounded-md bg-gray-100 text-gray-600">
              {work.parliament?.replace("_", " ") || "UNKNOWN"}
            </span>
            {/* Live ML Trained Model Risk Tag */}
            <span
              className={`text-[10px] uppercase font-extrabold px-2 py-0.5 rounded-md flex items-center gap-1 ${
                riskTier === "CRITICAL"
                  ? "bg-purple-50 text-purple-700 border border-purple-200"
                  : riskTier === "HIGH"
                  ? "bg-red-50 text-red-700 border border-red-200"
                  : riskTier === "MEDIUM"
                  ? "bg-amber-50 text-amber-700 border border-amber-200"
                  : "bg-emerald-50 text-emerald-700 border border-emerald-200"
              }`}
            >
              <ShieldCheck className="w-3 h-3" /> ML {riskTier} RISK
              {anomalyScore && (riskTier === "HIGH" || riskTier === "CRITICAL") && (
                <span className="opacity-70">({anomalyScore}%)</span>
              )}
            </span>
          </div>
          <span
            className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${getStatusBadge(
              work.lifecycle_status
            )}`}
          >
            {work.lifecycle_status}
          </span>
        </div>

        {/* Project Title / Description */}
        <h3 className="font-headline font-bold text-gray-900 text-base leading-snug line-clamp-2 group-hover:text-primary transition-colors mb-2">
          {work.work_description || "MPLADS Infrastructure Project"}
        </h3>

        {/* MP & Location Details */}
        <div className="space-y-1.5 text-xs text-gray-600 mb-4">
          <div className="flex items-center gap-1.5">
            <User className="w-3.5 h-3.5 text-primary shrink-0" />
            <span className="font-bold text-gray-800 truncate">{work.mp_name}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-secondary shrink-0" />
            <span className="truncate">
              {displayConstituency ? `${displayConstituency}, ` : ""}{work.state}
            </span>
          </div>
        </div>
      </div>

      {/* Financial Breakdown & Utilization */}
      <div className="border-t pt-3 mt-2 space-y-3">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-50/70 p-2.5 rounded-xl border border-gray-100">
            <span className="text-[10px] text-gray-400 uppercase font-bold block">Sanctioned</span>
            <span className="font-headline font-bold text-gray-900 text-sm">
              {formatCurrency(work.sanctioned_amount)}
            </span>
          </div>
          <div className="bg-gray-50/70 p-2.5 rounded-xl border border-gray-100">
            <span className="text-[10px] text-gray-400 uppercase font-bold block">Expenditure</span>
            <span className={`font-headline font-bold text-sm ${work.expenditure_amount && Number(work.expenditure_amount) > 0 ? "text-secondary" : "text-gray-500"}`}>
              {work.expenditure_amount && Number(work.expenditure_amount) > 0 ? formatCurrency(work.expenditure_amount) : (work.lifecycle_status === "SANCTIONED" ? "₹0 (Pending Release)" : "₹0")}
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div>
          <div className="flex justify-between text-[11px] font-bold text-gray-500 mb-1">
            <span>Fund Utilization</span>
            <span className={isOverBudget ? "text-red-600 font-black" : (utilizationPct === 0 ? "text-amber-600 font-medium" : "text-gray-700")}>
              {isOverBudget
                ? `⚠ ${((work.expenditure_to_sanction_ratio || 0) * 100).toFixed(1)}% Utilized (+${(((work.expenditure_to_sanction_ratio || 0) - 1) * 100).toFixed(1)}% over sanction)`
                : utilizationPct === 0
                ? "0.0% (Awaiting Disbursement)"
                : `${((work.expenditure_to_sanction_ratio || 0) * 100).toFixed(1)}%`
              }
            </span>
          </div>
          <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isOverBudget
                  ? "bg-red-500"
                  : work.lifecycle_status === "COMPLETED"
                  ? "bg-emerald-500"
                  : utilizationPct > 80
                  ? "bg-primary"
                  : "bg-amber-400"
              }`}
              style={{ width: `${Math.min(100, Math.max(0, utilizationPct))}%` }}
            />
          </div>
        </div>

        {/* Footer Meta & Buttons */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-[11px] text-gray-500 flex items-center gap-1 font-mono">
            {work.sanction_to_completion_days !== undefined && work.sanction_to_completion_days !== null ? (
              <>
                <Clock className="w-3.5 h-3.5 text-gray-400" />
                <span>{Math.abs(Number(work.sanction_to_completion_days))} days {Number(work.sanction_to_completion_days) < 0 ? "(Early)" : ""}</span>
              </>
            ) : (
              <span className="text-gray-400">Duration: Ongoing</span>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => onViewDetails(work)}
              className="px-2.5 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-bold transition-all flex items-center gap-1 shadow-sm active:scale-95"
              title="Quick Feature View"
            >
              <Eye className="w-3.5 h-3.5" /> Features
            </button>

            <Link
              href={`/projects/${encodeURIComponent(work.canonical_work_id)}?parliament=${work.parliament}`}
              className="px-3 py-1.5 rounded-lg bg-primary hover:bg-[var(--color-primary-hover)] text-white text-xs font-bold transition-all flex items-center gap-1 shadow-sm active:scale-95"
              title="Open Project Details Page"
            >
              <span>Open</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

