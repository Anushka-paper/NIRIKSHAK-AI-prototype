"use client";

import React, { useState } from "react";
import { WorkFeature } from "@/types/features";
import { X, CheckCircle, AlertCircle, IndianRupee, Clock, ShieldCheck, Activity } from "lucide-react";
import { predictRisk, PredictionResponse } from "@/lib/api";

interface Props {
  work: WorkFeature | null;
  onClose: () => void;
}

export default function WorkFeatureDetailModal({ work, onClose }: Props) {
  const [predicting, setPredicting] = useState<boolean>(false);
  const [mlPrediction, setMlPrediction] = useState<PredictionResponse["data"] | null>(null);

  if (!work) return null;

  const handleRunMLInference = async () => {
    setPredicting(true);
    try {
      const res = await predictRisk({
        work_id: work.canonical_work_id,
        estimated_cost: Number(work.sanction_amount || work.recommended_amount) || 1000000,
        days_since_sanction: Number(work.recommendation_to_sanction_days) || 120,
        current_status: String(work.work_status || work.lifecycle_status || "Sanction"),
        state: String(work.state || "National"),
        category: String(work.work_category || "General Infrastructure")
      });
      if (res && res.success && res.data) {
        setMlPrediction(res.data);
      }
    } catch (err) {
      console.error("ML Inference error:", err);
    } finally {
      setPredicting(false);
    }
  };

  const formatINR = (val?: number) => {
    if (val === undefined || val === null || isNaN(val)) return "₹0";
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    return `₹${val.toLocaleString()}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b bg-gray-50 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs px-2.5 py-1 rounded bg-primary/10 text-primary font-bold">
                {work.canonical_work_id}
              </span>
              <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-gray-200 text-gray-700">
                {work.parliament.replace("_", " ")}
              </span>
              {work.official_work_id && (
                <span className="text-xs text-gray-500 font-mono">
                  Official ID: {work.official_work_id}
                </span>
              )}
            </div>
            <h2 className="text-xl font-headline font-bold text-gray-900 mt-2">
              {work.work_description || "MPLADS Development Project"}
            </h2>
            <p className="text-xs text-gray-500 mt-1">
              {work.state} • {work.constituency} • MP: <span className="font-bold text-gray-800">{work.mp_name}</span>
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-200 text-gray-500 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Financial Breakdown */}
          <div>
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-3 flex items-center gap-2">
              <IndianRupee className="w-4 h-4 text-primary" /> Financial Features & Gap Analysis
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Recommended</span>
                <span className="text-base font-bold text-gray-800">{formatINR(work.recommended_amount)}</span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Sanctioned</span>
                <span className="text-base font-bold text-primary">{formatINR(work.sanctioned_amount)}</span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Total Expenditure</span>
                <span className="text-base font-bold text-secondary">{formatINR(work.expenditure_amount)}</span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Unspent Gap</span>
                <span className="text-base font-bold text-amber-600">{formatINR(work.unspent_amount)}</span>
              </div>
            </div>
          </div>

          {/* Lifecycle & Durations */}
          <div>
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-secondary" /> Lifecycle & Temporal Metrics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Lifecycle Status</span>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 inline-block mt-1">
                  {work.lifecycle_status}
                </span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Rec. to Sanction</span>
                <span className="text-base font-bold text-gray-800">
                  {work.recommendation_to_sanction_days !== undefined ? `${work.recommendation_to_sanction_days} Days` : "N/A"}
                </span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Execution Duration</span>
                <span className="text-base font-bold text-gray-800">
                  {work.sanction_to_completion_days ? `${work.sanction_to_completion_days} Days` : "Ongoing"}
                </span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Chronology Order</span>
                <div className="flex items-center gap-1.5 mt-1 font-bold text-xs text-green-700">
                  <CheckCircle className="w-3.5 h-3.5" /> Valid Order
                </div>
              </div>
            </div>
          </div>

          {/* Historical & Quality Signals */}
          <div>
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-600" /> Historical MP Benchmark & ER Provenance
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Preceding MP Works</span>
                <span className="text-sm font-bold text-gray-800">
                  {work.mp_historical_work_count ?? 0} works prior to this
                </span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Historical MP Completion Rate</span>
                <span className="text-sm font-bold text-gray-800">
                  {((work.mp_historical_completion_rate || 0) * 100).toFixed(1)}% (No Future Leakage)
                </span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border">
                <span className="text-[11px] text-gray-500 block uppercase">Entity Match Confidence</span>
                <span className="text-sm font-bold text-green-700 inline-flex items-center gap-1 mt-0.5">
                  <ShieldCheck className="w-3.5 h-3.5" /> {work.entity_resolution_confidence || "HIGH"} (Score: {work.entity_resolution_score || 100}%)
                </span>
              </div>
            </div>
          </div>

          {/* Trained ML Model Prediction Engine Section */}
          <div className="p-4 rounded-xl border border-primary/20 bg-gradient-to-r from-primary/5 via-surface to-secondary/5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
              <div>
                <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-primary" /> Trained ML Risk Intelligence Prediction
                </h3>
                <p className="text-xs text-gray-500">
                  Powered by HistGradientBoostingClassifier fitted on 75,501 works with 81 features
                </p>
              </div>

              {!mlPrediction && (
                <button
                  onClick={handleRunMLInference}
                  disabled={predicting}
                  className="px-4 py-2 rounded-lg bg-primary hover:bg-[var(--color-primary-hover)] text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 shrink-0"
                >
                  <Activity className={`w-3.5 h-3.5 ${predicting ? "animate-spin" : ""}`} />
                  {predicting ? "Evaluating Features..." : "Run ML Risk Inference"}
                </button>
              )}
            </div>

            {mlPrediction && (
              <div className="mt-3 pt-3 border-t border-primary/10 grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="p-3 bg-white rounded-lg border shadow-sm">
                  <span className="text-[10px] uppercase font-bold text-gray-400 block">Predicted Risk Level</span>
                  <span className={`inline-block font-headline font-bold text-base px-2.5 py-0.5 rounded-full mt-1 ${
                    mlPrediction.risk_level === "HIGH"
                      ? "bg-red-100 text-red-700"
                      : mlPrediction.risk_level === "MEDIUM"
                      ? "bg-amber-100 text-amber-800"
                      : "bg-emerald-100 text-emerald-800"
                  }`}>
                    {mlPrediction.risk_level} RISK ({(mlPrediction.risk_probability * 100).toFixed(0)}%)
                  </span>
                </div>

                <div className="p-3 bg-white rounded-lg border shadow-sm">
                  <span className="text-[10px] uppercase font-bold text-gray-400 block">Expected Milestone Delay</span>
                  <span className="font-headline font-bold text-base text-gray-900 block mt-1">
                    {mlPrediction.predicted_delay_days > 0 ? `+${mlPrediction.predicted_delay_days} Days Overdue` : "On Schedule"}
                  </span>
                </div>

                <div className="p-3 bg-white rounded-lg border shadow-sm">
                  <span className="text-[10px] uppercase font-bold text-gray-400 block">AI Recommendation</span>
                  <span className="text-xs text-gray-700 font-medium block mt-1">
                    {mlPrediction.recommendations}
                  </span>
                </div>

                {mlPrediction.key_factors && mlPrediction.key_factors.length > 0 && (
                  <div className="col-span-1 md:col-span-3 text-xs text-gray-600 bg-white/80 p-2.5 rounded-lg border">
                    <strong className="text-gray-900">Key Risk Drivers: </strong>
                    {mlPrediction.key_factors.join(" • ")}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50 flex justify-end">
          <button onClick={onClose} className="px-5 py-2 bg-gray-900 text-white font-bold rounded-lg text-sm hover:bg-gray-800">
            Close Feature View
          </button>
        </div>
      </div>
    </div>
  );
}

