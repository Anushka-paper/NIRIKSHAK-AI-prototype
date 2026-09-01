"use client";

import { useEffect, useState } from "react";
import { 
  Activity, 
  IndianRupee, 
  Map, 
  Users, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  FileCheck, 
  UserCheck, 
  Building2,
  Landmark,
  RefreshCw,
  Coins,
  ShieldCheck,
  ExternalLink
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [selectedHouse, setSelectedHouse] = useState<string>("all");
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [fetchError, setFetchError] = useState<boolean>(false);

  const fetchStats = async (house: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/dashboard/overview?house=${house}`);
      
      if (res.ok) {
        const data = await res.json();
        setStats(data);
        setFetchError(false);
      }
    } catch (err) {
      console.warn("Backend poll warning (retrying...):", err);
      setFetchError(true);
    }
  };

  useEffect(() => {
    fetchStats(selectedHouse);
  }, [selectedHouse]);

  if (fetchError && !stats) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950 text-white p-6">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 max-w-md text-center shadow-2xl">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4 animate-bounce" />
          <h2 className="text-xl font-bold text-white mb-2">Connecting to NIRIKSHAK Backend...</h2>
          <p className="text-gray-400 text-sm mb-6">
            The FastAPI live server is starting or syncing. Please click Retry to connect.
          </p>
          <button
            onClick={() => fetchStats(selectedHouse)}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl text-sm transition"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950 text-white">
        Loading data...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      {/* Header */}
      <header className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-800 pb-6">
        <div>
          <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-600">
            NIRIKSHAK AI
          </h1>
          <p className="text-gray-400 mt-1">MPLADS Sentinel — Real-Time Governance & Live eSAKSHI Dashboard</p>
        </div>

        {/* House Filter Toggle & Status Badge */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="bg-gray-900 border border-gray-800 p-1 rounded-xl flex items-center gap-1 shadow-inner">
            <button
              onClick={() => setSelectedHouse("all")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition ${
                selectedHouse === "all"
                  ? "bg-blue-600 text-white shadow"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              <Landmark className="w-3.5 h-3.5" /> All Houses
            </button>

            <button
              onClick={() => setSelectedHouse("lok_sabha")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition ${
                selectedHouse === "lok_sabha"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              <Building2 className="w-3.5 h-3.5" /> Lok Sabha
            </button>

            <button
              onClick={() => setSelectedHouse("rajya_sabha")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition ${
                selectedHouse === "rajya_sabha"
                  ? "bg-purple-600 text-white shadow"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              <Building2 className="w-3.5 h-3.5" /> Rajya Sabha
            </button>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-3.5 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded-full text-xs font-semibold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span> Dynamic House Query Engine
            </span>
          </div>
        </div>
      </header>

      {/* Currently Selected House Banner */}
      <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 bg-blue-950/30 border border-blue-900/40 rounded-xl px-5 py-3 text-sm">
        <div className="flex items-center gap-2 text-blue-300 font-medium">
          <Landmark className="w-4 h-4 text-blue-400" />
          <span>Viewing Live Data For: <strong className="text-white font-bold">{stats.house_label}</strong></span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <span>Tracking {stats.total_works.toLocaleString()} recommended works across {stats.total_mps} MPs</span>
          <a 
            href="https://mplads.mospi.gov.in/digigov/dashboard.html" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-blue-400 hover:text-blue-300 underline font-semibold transition"
          >
            Source: eSAKSHI MoSPI <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Official eSAKSHI Core Program Tile Cards */}
      <h2 className="text-lg font-semibold text-gray-300 mb-4 flex items-center gap-2">
        <Map className="w-5 h-5 text-blue-400" /> Live eSAKSHI Program Metrics ({stats.house_label})
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {/* 1. Allocated Limit */}
        <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl hover:border-gray-700 transition">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Allocated Limit for Hon'ble MPs</h3>
            <Coins className="text-amber-400 w-6 h-6" />
          </div>
          <p className="text-3xl font-extrabold text-white">₹ {stats.allocated_limit_cr.toLocaleString()} Crore</p>
          <p className="text-xs text-amber-400/80 mt-2 font-medium">Total entitlement allocated under MPLADS</p>
        </div>

        {/* 2. Amount Consented for Calamity */}
        <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl hover:border-gray-700 transition">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Amount Consented for Calamity</h3>
            <ShieldCheck className="text-cyan-400 w-6 h-6" />
          </div>
          <p className="text-3xl font-extrabold text-white">₹ {stats.calamity_consent_cr} Crore</p>
          <p className="text-xs text-cyan-400/80 mt-2 font-medium">Disaster relief fund consents</p>
        </div>

        {/* 3. Works Recommended */}
        <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl hover:border-gray-700 transition">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Works Recommended</h3>
            <Map className="text-blue-400 w-6 h-6" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-xs font-bold text-blue-400">No. {stats.total_works.toLocaleString()}</span>
            <p className="text-3xl font-extrabold text-white">₹ {stats.total_budget_cr.toLocaleString()} Crore</p>
          </div>
          <p className="text-xs text-gray-500 mt-2">Projects recommended online by MPs</p>
        </div>

        {/* 4. Works Sanctioned */}
        <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl hover:border-gray-700 transition">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Works Sanctioned</h3>
            <FileCheck className="text-indigo-400 w-6 h-6" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-xs font-bold text-indigo-400">No. {stats.sanctioned_works_count.toLocaleString()}</span>
            <p className="text-3xl font-extrabold text-white">₹ {stats.sanctioned_budget_cr.toLocaleString()} Crore</p>
          </div>
          <p className="text-xs text-indigo-400/80 mt-2 font-medium">Approved by District Authorities (IDAs)</p>
        </div>

        {/* 5. Works Completed */}
        <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl hover:border-gray-700 transition">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Works Completed</h3>
            <CheckCircle2 className="text-emerald-400 w-6 h-6" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-xs font-bold text-emerald-400">No. {stats.completed_works_count.toLocaleString()}</span>
            <p className="text-3xl font-extrabold text-white">₹ {stats.completed_budget_cr.toLocaleString()} Crore</p>
          </div>
          <p className="text-xs text-emerald-400/80 mt-2 font-medium">Physically completed & verified</p>
        </div>

        {/* 6. Expenditure Disbursed */}
        <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl hover:border-gray-700 transition">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Expenditure on Completed/On-going</h3>
            <IndianRupee className="text-purple-400 w-6 h-6" />
          </div>
          <p className="text-3xl font-extrabold text-white">₹ {stats.total_expenditure_cr.toLocaleString()} Crore</p>
          <p className="text-xs text-purple-400/80 mt-2 font-medium">Disbursed to contractors as on date</p>
        </div>
      </div>

      {/* Sentinel Security & Audit Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-red-950/20 border border-red-900/40 rounded-xl p-5 flex items-center justify-between">
          <div>
            <h4 className="text-xs text-red-400 font-semibold uppercase tracking-wider">High Risk Sentinel Flagged</h4>
            <p className="text-2xl font-bold text-white mt-1">{stats.high_risk_works.toLocaleString()} Works</p>
          </div>
          <ShieldAlert className="w-8 h-8 text-red-500" />
        </div>

        <div className="bg-yellow-950/20 border border-yellow-900/40 rounded-xl p-5 flex items-center justify-between">
          <div>
            <h4 className="text-xs text-yellow-400 font-semibold uppercase tracking-wider">Data Quality Audit Issues</h4>
            <p className="text-2xl font-bold text-white mt-1">{stats.data_quality_issues} Flags</p>
          </div>
          <AlertTriangle className="w-8 h-8 text-yellow-500" />
        </div>

        <div className="bg-blue-950/20 border border-blue-900/40 rounded-xl p-5 flex items-center justify-between">
          <div>
            <h4 className="text-xs text-blue-400 font-semibold uppercase tracking-wider">Active Tracked MPs</h4>
            <p className="text-2xl font-bold text-white mt-1">{stats.total_mps} Parliamentarians</p>
          </div>
          <UserCheck className="w-8 h-8 text-blue-400" />
        </div>
      </div>
    </div>
  );
}
