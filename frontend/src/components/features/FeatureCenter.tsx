"use client";

import React, { useState, useEffect } from "react";
import { DimensionAggregations, FeatureQualityAudit } from "@/types/features";
import { fetchDimensionAggregations, fetchFeatureQualityAudit } from "@/lib/featureService";
import { Database, ShieldCheck, AlertTriangle, Layers, BookOpen } from "lucide-react";
import FeatureCatalogModal from "./FeatureCatalogModal";

export default function FeatureCenter() {
  const [parliament, setParliament] = useState<string>("lok_sabha");
  const [tab, setTab] = useState<"aggregations" | "quality">("aggregations");
  const [catalogOpen, setCatalogOpen] = useState<boolean>(false);
  const [aggregations, setAggregations] = useState<DimensionAggregations | null>(null);
  const [qualityAudit, setQualityAudit] = useState<FeatureQualityAudit | null>(null);
  const [loadingAggs, setLoadingAggs] = useState<boolean>(false);

  useEffect(() => {
    if (tab === "aggregations") {
      setLoadingAggs(true);
      fetchDimensionAggregations(parliament)
        .then((data) => setAggregations(data))
        .catch((e) => console.error(e))
        .finally(() => setLoadingAggs(false));
    } else if (tab === "quality") {
      setLoadingAggs(true);
      fetchFeatureQualityAudit(parliament)
        .then((data) => setQualityAudit(data))
        .catch((e) => console.error(e))
        .finally(() => setLoadingAggs(false));
    }
  }, [parliament, tab]);

  return (
    <section className="bg-surface rounded-xl p-8 shadow-medium border border-gray-100 flex flex-col gap-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Database className="w-6 h-6 text-primary" />
            <h2 className="font-headline font-bold text-2xl text-gray-900">
              MPLADS Feature & Dimension Intelligence
            </h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Browse 118 engineered ML features, leak-safe historical benchmarks, and dimension aggregations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Parliament Toggle */}
          <div className="bg-gray-100 p-1 rounded-lg flex text-xs font-bold">
            <button
              onClick={() => setParliament("lok_sabha")}
              className={`px-3 py-1.5 rounded-md transition-all ${
                parliament === "lok_sabha" ? "bg-white text-primary shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Lok Sabha
            </button>
            <button
              onClick={() => setParliament("rajya_sabha")}
              className={`px-3 py-1.5 rounded-md transition-all ${
                parliament === "rajya_sabha" ? "bg-white text-primary shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Rajya Sabha
            </button>
          </div>

          {/* Open Dictionary Button */}
          <button
            onClick={() => setCatalogOpen(true)}
            className="px-3 py-2 bg-primary hover:bg-[var(--color-primary-hover)] text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <BookOpen className="w-4 h-4" /> Feature Catalog
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b text-sm font-semibold text-gray-500 gap-6">
        <button
          onClick={() => setTab("aggregations")}
          className={`pb-3 border-b-2 transition-all ${
            tab === "aggregations" ? "border-primary text-primary font-bold" : "border-transparent hover:text-gray-900"
          }`}
        >
          MP & State Performance Dimensions
        </button>
        <button
          onClick={() => setTab("quality")}
          className={`pb-3 border-b-2 transition-all ${
            tab === "quality" ? "border-primary text-primary font-bold" : "border-transparent hover:text-gray-900"
          }`}
        >
          Data Quality & Leakage Safety Audit
        </button>
      </div>

      {tab === "aggregations" && (
        <div className="space-y-6">
          {loadingAggs ? (
            <div className="py-12 text-center text-gray-400 text-sm">Loading dimension tables...</div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top MPs Table */}
              <div className="border rounded-xl p-5 bg-white shadow-subtle">
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 mb-3 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-primary" /> Top MP Performance Aggregates
                </h3>
                <div className="overflow-x-auto max-h-72">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-gray-50 uppercase text-gray-500 font-bold border-b sticky top-0">
                      <tr>
                        <th className="p-2">MP Name</th>
                        <th className="p-2">State</th>
                        <th className="p-2">Works</th>
                        <th className="p-2">Completed</th>
                        <th className="p-2">Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {aggregations?.mps.map((m, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="p-2 font-semibold text-gray-800">{m.mp_name}</td>
                          <td className="p-2 text-gray-500">{m.state}</td>
                          <td className="p-2 font-bold">{m.work_count}</td>
                          <td className="p-2 text-green-700 font-bold">{m.completed_work_count}</td>
                          <td className="p-2 font-bold">{(m.completion_rate * 100).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* State Aggregations Table */}
              <div className="border rounded-xl p-5 bg-white shadow-subtle">
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 mb-3 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-secondary" /> State Utilization Aggregates
                </h3>
                <div className="overflow-x-auto max-h-72">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-gray-50 uppercase text-gray-500 font-bold border-b sticky top-0">
                      <tr>
                        <th className="p-2">State</th>
                        <th className="p-2">Total Works</th>
                        <th className="p-2">Completed</th>
                        <th className="p-2">Expenditure Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {aggregations?.states.map((s, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="p-2 font-semibold text-gray-800">{s.state}</td>
                          <td className="p-2 font-bold">{s.work_count}</td>
                          <td className="p-2 text-green-700 font-bold">{s.completed_work_count}</td>
                          <td className="p-2 font-bold">{(s.completion_rate * 100).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === "quality" && (
        <div className="space-y-6">
          {loadingAggs ? (
            <div className="py-12 text-center text-gray-400 text-sm">Loading audit report...</div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Leakage Audit */}
              <div className="border rounded-xl p-5 bg-white shadow-subtle">
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 mb-3 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-green-600" /> Target Leakage Safety Check
                </h3>
                <div className="overflow-x-auto max-h-80">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-gray-50 uppercase text-gray-500 font-bold border-b sticky top-0">
                      <tr>
                        <th className="p-2">Feature</th>
                        <th className="p-2">Leakage Status</th>
                        <th className="p-2">Audit Rationale</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {qualityAudit?.leakage_audit.map((l, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="p-2 font-mono font-medium text-gray-800">{l.feature_name}</td>
                          <td className="p-2">
                            <span
                              className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                                l.leakage_status === "AVAILABLE_AT_PREDICTION"
                                  ? "bg-green-100 text-green-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}
                            >
                              {l.leakage_status}
                            </span>
                          </td>
                          <td className="p-2 text-gray-500">{l.rationale}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Quality Audit */}
              <div className="border rounded-xl p-5 bg-white shadow-subtle">
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" /> Feature Quality & Variance Audit
                </h3>
                <div className="overflow-x-auto max-h-80">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-gray-50 uppercase text-gray-500 font-bold border-b sticky top-0">
                      <tr>
                        <th className="p-2">Feature Name</th>
                        <th className="p-2">Status</th>
                        <th className="p-2">Missing %</th>
                        <th className="p-2">Audit Notes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {qualityAudit?.quality_audit.map((q, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="p-2 font-mono font-medium text-gray-800">{q.feature_name}</td>
                          <td className="p-2">
                            <span
                              className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                                q.quality_status === "HEALTHY"
                                  ? "bg-green-100 text-green-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}
                            >
                              {q.quality_status}
                            </span>
                          </td>
                          <td className="p-2 font-semibold">{q.missing_percentage}%</td>
                          <td className="p-2 text-gray-500">{q.audit_notes}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Feature Catalog Modal */}
      <FeatureCatalogModal
        isOpen={catalogOpen}
        onClose={() => setCatalogOpen(false)}
        parliament={parliament}
      />
    </section>
  );
}

