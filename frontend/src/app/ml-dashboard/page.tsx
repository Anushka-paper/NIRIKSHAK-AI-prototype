"use client";

import React, { useEffect, useState } from "react";
import AnomalyTable from "../../components/AnomalyTable";
import ForecastChart from "../../components/ForecastChart";
import { Activity, ShieldAlert, BarChart3, Network, Download, CheckCircle2 } from "lucide-react";

export default function MLDashboard() {
  const [reportGenerated, setReportGenerated] = useState(false);
  const [anomalySummary, setAnomalySummary] = useState<{total: number; critical: number; flagged: number} | null>(null);

  useEffect(() => {
    // Load summary stats for vendor collusion panel
    fetch("/api/anomalies/summary?parliament=all")
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d) {
          setAnomalySummary({
            total: d.total_works ?? 0,
            critical: d.critical_anomalies ?? 0,
            flagged: d.flagged_works ?? 0,
          });
        }
      })
      .catch(() => {});
  }, []);

  const handleGenerateReport = () => {
    // Trigger CSV download of anomaly data
    const url = "/api/anomalies?parliament=all&limit=10000&format=csv";
    const link = document.createElement("a");
    link.href = url;
    link.download = `nirikshak_anomaly_report_${new Date().toISOString().split("T")[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setReportGenerated(true);
    setTimeout(() => setReportGenerated(false), 3000);
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 flex items-center gap-3">
              <ShieldAlert className="text-indigo-600" size={32} />
              Nirikshak 2.0 ML Intelligence
            </h1>
            <p className="text-gray-500 mt-1">Real-time anomaly detection and predictive forecasting</p>
          </div>

          <div className="flex gap-4">
            <div className="bg-white px-4 py-2 rounded-lg shadow-sm border border-gray-200 flex items-center gap-2">
              <Activity className="text-green-500 animate-pulse" size={18} />
              <span className="text-sm font-medium">System Active</span>
            </div>
            <button
              onClick={handleGenerateReport}
              className={`px-4 py-2 rounded-lg shadow-sm flex items-center gap-2 font-medium transition cursor-pointer ${
                reportGenerated
                  ? "bg-green-600 text-white"
                  : "bg-indigo-600 hover:bg-indigo-700 text-white"
              }`}
            >
              {reportGenerated ? (
                <><CheckCircle2 size={18} /> Report Downloaded</>
              ) : (
                <><Download size={18} /> Generate Report</>
              )}
            </button>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
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
        <section className="bg-gradient-to-r from-slate-800 to-indigo-900 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-start gap-4">
            <Network className="text-indigo-300 mt-1 shrink-0" size={28} />
            <div>
              <h3 className="text-2xl font-bold mb-2">Vendor Collusion Graph Active</h3>
              <p className="text-indigo-200 max-w-3xl">
                The NetworkX bipartite graph model is continuously analyzing{" "}
                <strong className="text-white">
                  {anomalySummary ? anomalySummary.total.toLocaleString() : "…"} active projects
                </strong>{" "}
                across all parliaments. Works with anomaly scores ≥ 70% are flagged as potential risk vectors.{" "}
                <strong className="text-amber-300">
                  {anomalySummary ? anomalySummary.flagged.toLocaleString() : "…"} works flagged
                </strong>{" "}
                — including{" "}
                <strong className="text-red-300">
                  {anomalySummary ? anomalySummary.critical.toLocaleString() : "…"} critical anomalies
                </strong>{" "}
                — for investigation.
              </p>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
