"use client";

import { useEffect, useState } from "react";
import { Activity, IndianRupee, Map, Users } from "lucide-react";

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/v1/dashboard/overview")
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((err) => console.error("Error fetching stats:", err));
  }, []);

  if (!stats) return <div className="flex h-screen items-center justify-center bg-gray-950 text-white">Loading data...</div>;

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-600">
          NIRIKSHAK AI
        </h1>
        <p className="text-gray-400 mt-2">MPLADS Sentinel - Live Dashboard</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total Works */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-400 font-medium">Total Works</h3>
            <Map className="text-blue-500 w-5 h-5" />
          </div>
          <p className="text-3xl font-bold">{stats.total_works.toLocaleString()}</p>
        </div>

        {/* Total Budget */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-400 font-medium">Sanctioned Budget</h3>
            <IndianRupee className="text-green-500 w-5 h-5" />
          </div>
          <p className="text-3xl font-bold">₹{stats.total_budget_cr} Cr</p>
        </div>

        {/* Total Expenditure */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-400 font-medium">Utilized Funds</h3>
            <Activity className="text-purple-500 w-5 h-5" />
          </div>
          <p className="text-3xl font-bold">₹{stats.total_expenditure_cr} Cr</p>
          <p className="text-sm text-gray-500 mt-1">{stats.utilization_pct}% utilization</p>
        </div>

        {/* Active Vendors */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-400 font-medium">Active Vendors</h3>
            <Users className="text-orange-500 w-5 h-5" />
          </div>
          <p className="text-3xl font-bold">{stats.total_vendors.toLocaleString()}</p>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg h-96 flex flex-col items-center justify-center">
        <h3 className="text-xl font-bold mb-4">Risk & ML Insights (Coming Soon)</h3>
        <p className="text-gray-400 text-center max-w-lg">
          This dashboard is currently displaying raw data from our data pipeline (Phase 2).
          In Phase 3-8, the Python backend will run anomaly detection, duplicate NLP checking, and trend analysis.
          The visual charts for those insights will appear here!
        </p>
      </div>
    </div>
  );
}
