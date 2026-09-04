import React from "react";
import AnomalyTable from "../../components/AnomalyTable";
import ForecastChart from "../../components/ForecastChart";
import { Activity, ShieldAlert, BarChart3 } from "lucide-react";

export default function MLDashboard() {
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
            <div className="bg-indigo-600 text-white px-4 py-2 rounded-lg shadow-sm flex items-center gap-2 font-medium hover:bg-indigo-700 transition cursor-pointer">
              <BarChart3 size={18} />
              Generate Report
            </div>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Anomalies */}
          <section className="space-y-4">
            <AnomalyTable />
          </section>

          {/* Right Column - Forecasting */}
          <section className="space-y-4">
            <ForecastChart entityId="ALL" />
          </section>
        </div>

        {/* Additional ML Insights can go here */}
        <section className="bg-gradient-to-r from-slate-800 to-indigo-900 rounded-2xl p-8 text-white shadow-xl">
          <h3 className="text-2xl font-bold mb-2">Vendor Collusion Graph Active</h3>
          <p className="text-indigo-200 max-w-3xl">
            The NetworkX bipartite graph model is currently analyzing 3,450 active projects and 1,200 vendors in the background. High centrality scores will automatically flag potential cartel formations in your alerts panel.
          </p>
        </section>

      </div>
    </div>
  );
}
