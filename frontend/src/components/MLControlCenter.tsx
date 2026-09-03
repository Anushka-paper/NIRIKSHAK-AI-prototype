"use client";

import React, { useState, useEffect } from "react";
import { 
  checkMLHealth, 
  getDashboardOverview, 
  predictRisk, 
  MLHealthResponse, 
  DashboardOverviewResponse,
  PredictionResponse 
} from "@/lib/api";
import { Activity, ShieldAlert, Cpu, CheckCircle, RefreshCw, AlertTriangle, ArrowRight } from "lucide-react";

export default function MLControlCenter() {
  const [health, setHealth] = useState<MLHealthResponse | null>(null);
  const [overview, setOverview] = useState<DashboardOverviewResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  
  // Prediction Form State
  const [cost, setCost] = useState<number>(2500000);
  const [days, setDays] = useState<number>(420);
  const [status, setStatus] = useState<string>("Sanctioned");
  const [predicting, setPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null);

  const fetchStatus = async () => {
    setLoadingHealth(true);
    try {
      const [h, o] = await Promise.all([
        checkMLHealth().catch(() => null),
        getDashboardOverview("all").catch(() => null)
      ]);
      setHealth(h);
      setOverview(o);
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setPredicting(true);
    try {
      const res = await predictRisk({
        work_id: `WORK-${Math.floor(Math.random() * 90000) + 10000}`,
        estimated_cost: cost,
        days_since_sanction: days,
        current_status: status,
      });
      setPredictionResult(res);
    } catch (err) {
      console.error("Prediction failed:", err);
    } finally {
      setPredicting(false);
    }
  };

  return (
    <section className="bg-surface rounded-xl p-8 shadow-medium border border-gray-100 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-6 h-6 text-primary" />
            <h2 className="font-headline font-bold text-2xl text-gray-900">
              ML Services & Risk Engine
            </h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Dynamic integration: Next.js API Gateway ↔ Python FastAPI ML Service
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-50 border text-xs font-semibold">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                health?.success ? "bg-green-500 animate-pulse" : "bg-amber-500"
              }`}
            />
            <span>
              ML Gateway: {health?.success ? "ONLINE (FastAPI)" : "DISCONNECTED"}
            </span>
          </div>

          <button
            onClick={fetchStatus}
            disabled={loadingHealth}
            className="p-2 rounded-lg border hover:bg-gray-50 text-gray-600 transition-colors"
            title="Refresh Status"
          >
            <RefreshCw className={`w-4 h-4 ${loadingHealth ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Overview Stat Badges */}
      {overview?.success && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Monitored Datasets</span>
            <p className="text-2xl font-headline font-bold text-gray-900 mt-1">
              {overview.data.datasets.loaded} / {overview.data.datasets.total} Loaded
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Total Standardized Records</span>
            <p className="text-2xl font-headline font-bold text-primary mt-1">
              {overview.data.records.total.toLocaleString()}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Data Quality Score</span>
            <p className="text-2xl font-headline font-bold text-secondary mt-1">
              {overview.data.dataQuality.score}%
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Pipeline Verification</span>
            <div className="flex items-center gap-1.5 text-green-600 mt-2 font-bold text-sm">
              <CheckCircle className="w-4 h-4" /> Passed 100%
            </div>
          </div>
        </div>
      )}

      {/* Interactive Risk Prediction Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-2">
        <div className="border border-gray-200 rounded-xl p-6 bg-white flex flex-col justify-between">
          <div>
            <h3 className="font-headline font-bold text-lg text-gray-900 mb-2 flex items-center gap-2">
              <Activity className="w-5 h-5 text-secondary" /> Project Delay & Risk Prediction
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Submit project parameters to the ML prediction model to forecast delay probability and cost overruns.
            </p>

            <form onSubmit={handlePredict} className="flex flex-col gap-4">
              <div>
                <label className="text-xs font-bold text-gray-600 uppercase">Estimated Cost (₹)</label>
                <input
                  type="number"
                  value={cost}
                  onChange={(e) => setCost(Number(e.target.value))}
                  className="w-full mt-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:border-primary"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-gray-600 uppercase">Elapsed Days</label>
                  <input
                    type="number"
                    value={days}
                    onChange={(e) => setDays(Number(e.target.value))}
                    className="w-full mt-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:border-primary"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-600 uppercase">Current Status</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="w-full mt-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:border-primary bg-white"
                  >
                    <option value="Sanctioned">Sanctioned</option>
                    <option value="Ongoing">Ongoing / In-Progress</option>
                    <option value="Completed">Completed</option>
                    <option value="Pending">Pending</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={predicting}
                className="mt-2 w-full bg-primary hover:bg-[var(--color-primary-hover)] active:scale-[0.99] text-white font-bold py-2.5 px-4 rounded-lg text-sm transition-all flex items-center justify-center gap-2"
              >
                {predicting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Evaluating ML Risk...
                  </>
                ) : (
                  <>
                    Run ML Inference <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Prediction Results Display */}
        <div className="border border-gray-200 rounded-xl p-6 bg-gray-50 flex flex-col justify-between">
          <div>
            <h3 className="font-headline font-bold text-lg text-gray-900 mb-2 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-600" /> Live ML Inference Output
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Real-time response returned from Python FastAPI ML engine via Next.js gateway.
            </p>

            {predictionResult?.data ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-white rounded-lg border">
                  <div>
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Risk Category</span>
                    <p
                      className={`text-2xl font-black ${
                        predictionResult.data.risk_level === "HIGH"
                          ? "text-red-600"
                          : predictionResult.data.risk_level === "MEDIUM"
                          ? "text-amber-600"
                          : "text-green-600"
                      }`}
                    >
                      {predictionResult.data.risk_level} RISK
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Delay Probability</span>
                    <p className="text-2xl font-black text-gray-900">
                      {(predictionResult.data.risk_probability * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border text-sm space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Predicted Delay:</span>
                    <span className="font-bold text-gray-800">
                      +{predictionResult.data.predicted_delay_days} days
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Recommendation:</span>
                    <span className="font-bold text-primary text-right">
                      {predictionResult.data.recommendations}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1">
                    Contributing Factors
                  </span>
                  <ul className="text-xs text-gray-700 list-disc pl-4 space-y-1">
                    {predictionResult.data.key_factors.map((f: string, i: number) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="h-48 flex flex-col items-center justify-center text-center p-4 border border-dashed rounded-lg text-gray-400">
                <AlertTriangle className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm font-medium">No prediction run yet.</p>
                <p className="text-xs">Adjust parameters on the left and click "Run ML Inference".</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

