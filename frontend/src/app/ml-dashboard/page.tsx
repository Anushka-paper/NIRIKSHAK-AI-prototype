"use client";

import React, { useEffect, useState } from "react";
import AnomalyTable from "../../components/AnomalyTable";
import ForecastChart from "../../components/ForecastChart";
import { Activity, ShieldAlert, BarChart3, Network, Download, CheckCircle2 } from "lucide-react";
import { useRequireAuth } from "@/lib/authContext";

export default function MLDashboard() {
  const { user, loading: authLoading } = useRequireAuth();
  const [reportGenerated, setReportGenerated] = useState(false);
  const [anomalySummary, setAnomalySummary] = useState<{total: number; critical: number; flagged: number} | null>(null);
  // null = still checking, true = last call succeeded, false = it failed --
  // the "System Active" badge below reflects this instead of being a
  // hardcoded decoration with no real signal behind it.
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    if (!user) return;
    // Load summary stats for vendor collusion panel
    fetch("/api/anomalies/summary?parliament=all")
      .then(r => r.ok ? r.json() : null)
      .then(json => {
        // The proxy route wraps the backend payload as {success, data},
        // it doesn't forward the raw shape -- reading fields off the
        // envelope itself (not .data) silently produced all-zero stats.
        const d = json?.data;
        if (json?.success && d) {
          setAnomalySummary({
            total: d.total_works ?? 0,
            critical: d.critical_anomalies ?? 0,
            flagged: d.flagged_works ?? 0,
          });
          setApiHealthy(true);
        } else {
          setApiHealthy(false);
        }
      })
      .catch(() => setApiHealthy(false));
  }, [user]);

  const handleGenerateReport = () => {
    // Trigger CSV download of anomaly data
    const url = "/api/anomalies?parliament=all&limit=10000&format=csv";
    const link = document.createElement("a");
    link.href = url;
    link.download = `nirikshak_anomaly_report_${new Date().toISOString().split("T")[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setReportGenerated(true);
    setTimeout(() => setReportGenerated(false), 3000);
  };

  if (authLoading || !user) {
    return <div className="py-24 text-center text-sm text-gray-500">Loading...</div>;
  }

  return (
    <div className="flex flex-col gap-8 font-body pb-16">
      {/* Header */}
      <div className="bg-white rounded-3xl p-8 border border-gray-100 shadow-subtle flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="font-headline font-extrabold text-3xl md:text-4xl text-gray-900 tracking-tight flex items-center gap-3">
            <ShieldAlert className="text-primary" size={32} />
            Nirikshak 2.0 ML Intelligence
          </h1>
          <p className="text-gray-500 text-sm md:text-base mt-1">Real-time anomaly detection and predictive forecasting</p>
        </div>

        <div className="flex gap-3">
          <div className="bg-white px-4 py-2 rounded-xl shadow-subtle border border-gray-200 flex items-center gap-2">
            <Activity className={`${apiHealthy === false ? "text-rose-500" : "text-emerald-500 animate-pulse"}`} size={18} />
            <span className="text-sm font-semibold">
              {apiHealthy === false ? "Backend Unreachable" : apiHealthy === true ? "System Active" : "Checking..."}
            </span>
          </div>
          <button
            onClick={handleGenerateReport}
            className={`px-4 py-2 rounded-xl shadow-sm flex items-center gap-2 font-bold text-sm transition cursor-pointer ${
              reportGenerated
                ? "bg-emerald-600 text-white"
                : "bg-primary hover:bg-[var(--color-primary-hover)] text-white"
            }`}
          >
            {reportGenerated ? (
              <><CheckCircle2 size={18} /> Report Downloaded</>
            ) : (
              <><Download size={18} /> Generate Report</>
            )}
          </button>
        </div>
      </div>

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Anomalies */}
        <section className="space-y-4">
          <AnomalyTable parliament="all" />
        </section>

        {/* Right Column - Forecasting */}
        <section className="space-y-4">
          <ForecastChart entityId="ALL" />
        </section>
      </div>

      {/* Vendor Collusion Graph Panel - dynamic data */}
      <section className="bg-gradient-to-r from-slate-900 to-primary/90 rounded-3xl p-8 text-white shadow-medium">
        <div className="flex items-start gap-4">
          <Network className="text-white/70 mt-1 shrink-0" size={28} />
          <div>
            <h3 className="font-headline text-2xl font-bold mb-2">Vendor Collusion Graph Active</h3>
            <p className="text-white/80 max-w-3xl text-sm md:text-base">
              The NetworkX bipartite graph model is continuously analyzing{" "}
              <strong className="text-white">
                {anomalySummary ? anomalySummary.total.toLocaleString() : "…"} active projects
              </strong>{" "}
              across all parliaments. Works with anomaly scores &ge; 70% are flagged as potential risk vectors.{" "}
              <strong className="text-amber-300">
                {anomalySummary ? anomalySummary.flagged.toLocaleString() : "…"} works flagged
              </strong>{" "}
              — including{" "}
              <strong className="text-rose-300">
                {anomalySummary ? anomalySummary.critical.toLocaleString() : "…"} critical anomalies
              </strong>{" "}
              — for investigation.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
