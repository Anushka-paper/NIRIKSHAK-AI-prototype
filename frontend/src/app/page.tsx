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
  ExternalLink,
  Search,
  Filter,
  Layers,
  Database,
  Sliders,
  CheckCircle,
  XCircle,
  FileText
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "compliance" | "works" | "features">("overview");
  const [stats, setStats] = useState<any>(null);
  const [selectedHouse, setSelectedHouse] = useState<string>("all");
  const [fetchError, setFetchError] = useState<boolean>(false);

  // Compliance Tab State
  const [complianceSummary, setComplianceSummary] = useState<any>(null);
  const [violations, setViolations] = useState<any[]>([]);
  const [selectedSeverity, setSelectedSeverity] = useState<string>("");
  const [complianceSearch, setComplianceSearch] = useState<string>("");

  // Master Works Tab State
  const [works, setWorks] = useState<any[]>([]);
  const [totalWorksCount, setTotalWorksCount] = useState<number>(0);
  const [workSearch, setWorkSearch] = useState<string>("");
  const [selectedStage, setSelectedStage] = useState<string>("");

  // Feature Store Tab State
  const [featureSummary, setFeatureSummary] = useState<any>(null);
  const [mpFeatures, setMpFeatures] = useState<any[]>([]);

  const fetchStats = async (house: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/dashboard/overview?house=${house}`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
        setFetchError(false);
      }
    } catch (err) {
      console.warn("Backend poll warning:", err);
      setFetchError(true);
    }
  };

  const fetchCompliance = async () => {
    try {
      const sumRes = await fetch(`${API_URL}/api/v1/compliance/summary`);
      if (sumRes.ok) setComplianceSummary(await sumRes.json());

      let url = `${API_URL}/api/v1/compliance/violations?limit=25`;
      if (selectedSeverity) url += `&severity=${selectedSeverity}`;
      if (complianceSearch) url += `&search=${encodeURIComponent(complianceSearch)}`;
      
      const violRes = await fetch(url);
      if (violRes.ok) {
        const data = await violRes.json();
        setViolations(data.violations || []);
      }
    } catch (err) {
      console.warn("Compliance fetch error:", err);
    }
  };

  const fetchMasterWorks = async () => {
    try {
      let url = `${API_URL}/api/v1/standardization/master-works?limit=25`;
      if (selectedHouse !== "all") url += `&house=${selectedHouse.toUpperCase()}`;
      if (selectedStage) url += `&lifecycle_stage=${selectedStage}`;
      if (workSearch) url += `&search=${encodeURIComponent(workSearch)}`;

      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setWorks(data.works || []);
        setTotalWorksCount(data.total || 0);
      }
    } catch (err) {
      console.warn("Works fetch error:", err);
    }
  };

  const fetchFeatures = async () => {
    try {
      const sumRes = await fetch(`${API_URL}/api/v1/features/summary`);
      if (sumRes.ok) setFeatureSummary(await sumRes.json());

      const mpRes = await fetch(`${API_URL}/api/v1/features/mp?limit=15`);
      if (mpRes.ok) {
        const data = await mpRes.json();
        setMpFeatures(data.records || []);
      }
    } catch (err) {
      console.warn("Features fetch error:", err);
    }
  };

  useEffect(() => {
    fetchStats(selectedHouse);
  }, [selectedHouse]);

  useEffect(() => {
    if (activeTab === "compliance") fetchCompliance();
    if (activeTab === "works") fetchMasterWorks();
    if (activeTab === "features") fetchFeatures();
  }, [activeTab, selectedHouse, selectedSeverity, complianceSearch, selectedStage, workSearch]);

  if (fetchError && !stats) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950 text-white p-6">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 max-w-md text-center shadow-2xl">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4 animate-bounce" />
          <h2 className="text-xl font-bold text-white mb-2">Connecting to NIRIKSHAK Backend...</h2>
          <p className="text-gray-400 text-sm mb-6">
            The FastAPI live server is starting. Click retry to verify connection.
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
      <div className="flex h-screen items-center justify-center bg-gray-950 text-white font-medium">
        <RefreshCw className="w-6 h-6 text-blue-500 animate-spin mr-3" /> Loading NIRIKSHAK Analytics Data...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 md:p-8">
      {/* Top Header Bar */}
      <header className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-800 pb-6">
        <div>
          <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-500">
            NIRIKSHAK AI
          </h1>
          <p className="text-gray-400 text-sm mt-1">MPLADS Sentinel — Real-Time Governance & Live Compliance Engine</p>
        </div>

        {/* House Filter Toggle */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
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
        </div>
      </header>

      {/* Primary Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-800 mb-6 overflow-x-auto pb-2">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 transition whitespace-nowrap ${
            activeTab === "overview"
              ? "bg-blue-600 text-white shadow-lg"
              : "bg-gray-900/60 text-gray-400 hover:text-white hover:bg-gray-800"
          }`}
        >
          <Activity className="w-4 h-4" /> eSAKSHI Program Metrics
        </button>

        <button
          onClick={() => setActiveTab("compliance")}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 transition whitespace-nowrap ${
            activeTab === "compliance"
              ? "bg-red-600 text-white shadow-lg"
              : "bg-gray-900/60 text-gray-400 hover:text-white hover:bg-gray-800"
          }`}
        >
          <ShieldAlert className="w-4 h-4 text-red-300" /> Compliance Audit Feed
          <span className="ml-1 px-2 py-0.5 bg-red-950 text-red-200 rounded-full text-[10px] border border-red-800">
            90,277 Flags
          </span>
        </button>

        <button
          onClick={() => setActiveTab("works")}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 transition whitespace-nowrap ${
            activeTab === "works"
              ? "bg-indigo-600 text-white shadow-lg"
              : "bg-gray-900/60 text-gray-400 hover:text-white hover:bg-gray-800"
          }`}
        >
          <Layers className="w-4 h-4" /> Master Works Explorer (243k)
        </button>

        <button
          onClick={() => setActiveTab("features")}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 transition whitespace-nowrap ${
            activeTab === "features"
              ? "bg-purple-600 text-white shadow-lg"
              : "bg-gray-900/60 text-gray-400 hover:text-white hover:bg-gray-800"
          }`}
        >
          <Database className="w-4 h-4" /> Canonical Feature Store (v1.0)
        </button>
      </div>

      {/* TAB 1: OVERVIEW METRICS */}
      {activeTab === "overview" && (
        <div>
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

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {/* 1. Allocated Limit */}
            <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl hover:border-gray-700 transition">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Allocated Limit for MPs</h3>
                <Coins className="text-amber-400 w-6 h-6" />
              </div>
              <p className="text-3xl font-extrabold text-white">₹ {stats.allocated_limit_cr.toLocaleString()} Crore</p>
              <p className="text-xs text-amber-400/80 mt-2 font-medium">Total entitlement allocated under MPLADS</p>
            </div>

            {/* 2. Amount Consented for Calamity */}
            <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl hover:border-gray-700 transition">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Calamity Consent Amount</h3>
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
                <p className="text-3xl font-extrabold text-white">₹ {stats.total_budget_cr.toLocaleString()} Cr</p>
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
                <p className="text-3xl font-extrabold text-white">₹ {stats.sanctioned_budget_cr.toLocaleString()} Cr</p>
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
                <p className="text-3xl font-extrabold text-white">₹ {stats.completed_budget_cr.toLocaleString()} Cr</p>
              </div>
              <p className="text-xs text-emerald-400/80 mt-2 font-medium">Physically completed & verified</p>
            </div>

            {/* 6. Expenditure Disbursed */}
            <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl hover:border-gray-700 transition">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Expenditure Disbursed</h3>
                <IndianRupee className="text-purple-400 w-6 h-6" />
              </div>
              <p className="text-3xl font-extrabold text-white">₹ {stats.total_expenditure_cr.toLocaleString()} Cr</p>
              <p className="text-xs text-purple-400/80 mt-2 font-medium">Disbursed to contractors as on date</p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: COMPLIANCE AUDIT FEED */}
      {activeTab === "compliance" && (
        <div>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <span className="text-xs text-gray-400 font-semibold uppercase">Total Violations Flagged</span>
              <p className="text-2xl font-extrabold text-white mt-1">
                {complianceSummary?.total_violations?.toLocaleString() || "90,277"}
              </p>
            </div>

            <div className="bg-red-950/30 border border-red-900/50 rounded-xl p-4">
              <span className="text-xs text-red-400 font-semibold uppercase">CRITICAL Flags (R003)</span>
              <p className="text-2xl font-extrabold text-red-400 mt-1">
                {complianceSummary?.severity_breakdown?.CRITICAL?.toLocaleString() || "71,056"}
              </p>
            </div>

            <div className="bg-amber-950/30 border border-amber-900/50 rounded-xl p-4">
              <span className="text-xs text-amber-400 font-semibold uppercase">HIGH Flags (R007)</span>
              <p className="text-2xl font-extrabold text-amber-400 mt-1">
                {complianceSummary?.severity_breakdown?.HIGH?.toLocaleString() || "6,460"}
              </p>
            </div>

            <div className="bg-blue-950/30 border border-blue-900/50 rounded-xl p-4">
              <span className="text-xs text-blue-400 font-semibold uppercase">MEDIUM Flags (R008)</span>
              <p className="text-2xl font-extrabold text-blue-400 mt-1">
                {complianceSummary?.severity_breakdown?.MEDIUM?.toLocaleString() || "12,761"}
              </p>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-gray-900 border border-gray-800 p-4 rounded-xl mb-6">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Filter className="w-4 h-4 text-gray-400" />
              <span className="text-xs text-gray-400 font-bold uppercase">Filter Severity:</span>
              {["", "CRITICAL", "HIGH", "MEDIUM"].map((sev) => (
                <button
                  key={sev}
                  onClick={() => setSelectedSeverity(sev)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                    selectedSeverity === sev
                      ? "bg-blue-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:text-white"
                  }`}
                >
                  {sev || "All"}
                </button>
              ))}
            </div>

            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search Work ID or Rule..."
                value={complianceSearch}
                onChange={(e) => setComplianceSearch(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 text-white text-xs rounded-xl pl-9 pr-4 py-2.5 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Violations Table */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-2xl">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="bg-gray-950 text-gray-400 uppercase font-semibold border-b border-gray-800">
                <tr>
                  <th className="p-4">Rule</th>
                  <th className="p-4">Severity</th>
                  <th className="p-4">Work / Entity ID</th>
                  <th className="p-4">State & MP</th>
                  <th className="p-4">Violation Details</th>
                  <th className="p-4">Recommended Human Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {violations.map((v, i) => (
                  <tr key={i} className="hover:bg-gray-800/40 transition">
                    <td className="p-4 font-mono font-bold text-blue-400">{v.rule_code}</td>
                    <td className="p-4">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                        v.severity === "CRITICAL"
                          ? "bg-red-950 text-red-400 border-red-800"
                          : v.severity === "HIGH"
                          ? "bg-amber-950 text-amber-400 border-amber-800"
                          : "bg-blue-950 text-blue-400 border-blue-800"
                      }`}>
                        {v.severity}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-gray-200">{v.entity_id}</td>
                    <td className="p-4">
                      <div className="font-semibold text-white">{v.state}</div>
                      <div className="text-[11px] text-gray-400">{v.mp_name}</div>
                    </td>
                    <td className="p-4 text-gray-200 max-w-xs">{v.description}</td>
                    <td className="p-4 text-amber-300/90 font-medium max-w-xs">{v.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: MASTER WORKS EXPLORER */}
      {activeTab === "works" && (
        <div>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-gray-900 border border-gray-800 p-4 rounded-xl mb-6">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 font-bold uppercase">Lifecycle Stage:</span>
              {["", "RECOMMENDED", "SANCTIONED", "IN_PROGRESS", "COMPLETED"].map((stg) => (
                <button
                  key={stg}
                  onClick={() => setSelectedStage(stg)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                    selectedStage === stg
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:text-white"
                  }`}
                >
                  {stg || "All"}
                </button>
              ))}
            </div>

            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search Title or MP..."
                value={workSearch}
                onChange={(e) => setWorkSearch(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 text-white text-xs rounded-xl pl-9 pr-4 py-2.5 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-2xl">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="bg-gray-950 text-gray-400 uppercase font-semibold border-b border-gray-800">
                <tr>
                  <th className="p-4">Work ID</th>
                  <th className="p-4">House & State</th>
                  <th className="p-4">MP Name</th>
                  <th className="p-4">Work Title / Description</th>
                  <th className="p-4">Category</th>
                  <th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {works.map((w, i) => (
                  <tr key={i} className="hover:bg-gray-800/40 transition">
                    <td className="p-4 font-mono font-bold text-indigo-400">{w.canonical_work_id}</td>
                    <td className="p-4">
                      <span className="font-semibold text-white">{w.source_house}</span>
                      <div className="text-[11px] text-gray-400">{w.canonical_state}</div>
                    </td>
                    <td className="p-4 font-medium text-gray-200">{w.canonical_mp_name}</td>
                    <td className="p-4 max-w-sm text-white font-medium truncate">{w.work}</td>
                    <td className="p-4 text-xs font-semibold text-gray-400">{w.canonical_work_category}</td>
                    <td className="p-4">
                      <span className="px-2.5 py-1 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded-full text-[10px] font-bold">
                        {w.lifecycle_stage}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: CANONICAL FEATURE STORE */}
      {activeTab === "features" && (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <span className="text-xs text-purple-400 font-semibold uppercase">features_work</span>
              <p className="text-2xl font-extrabold text-white mt-1">243,886</p>
              <span className="text-[11px] text-gray-500">Work Lifecycle Records</span>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <span className="text-xs text-purple-400 font-semibold uppercase">features_transaction</span>
              <p className="text-2xl font-extrabold text-white mt-1">107,981</p>
              <span className="text-[11px] text-gray-500">Disbursement Transactions</span>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <span className="text-xs text-purple-400 font-semibold uppercase">features_vendor</span>
              <p className="text-2xl font-extrabold text-white mt-1">21,177</p>
              <span className="text-[11px] text-gray-500">Vendor Master Entities</span>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <span className="text-xs text-purple-400 font-semibold uppercase">features_mp</span>
              <p className="text-2xl font-extrabold text-white mt-1">727</p>
              <span className="text-[11px] text-gray-500">Parliamentarian Entities</span>
            </div>
          </div>

          {/* MP Features Overview Table */}
          <h3 className="text-sm font-bold text-gray-300 mb-3 flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-purple-400" /> Parliamentarian Feature Store (`features_mp`)
          </h3>

          <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-2xl">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="bg-gray-950 text-gray-400 uppercase font-semibold border-b border-gray-800">
                <tr>
                  <th className="p-4">MP ID</th>
                  <th className="p-4">Parliamentarian</th>
                  <th className="p-4">House & State</th>
                  <th className="p-4">Utilisation %</th>
                  <th className="p-4">Output / Rupee (per Cr)</th>
                  <th className="p-4">Avg Sanction Delay</th>
                  <th className="p-4">Category Entropy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {mpFeatures.map((m, i) => (
                  <tr key={i} className="hover:bg-gray-800/40 transition">
                    <td className="p-4 font-mono font-bold text-purple-400">{m.mp_id}</td>
                    <td className="p-4 font-bold text-white">{m.canonical_name}</td>
                    <td className="p-4">
                      <div className="font-semibold text-gray-300">{m.source_house}</div>
                      <div className="text-[11px] text-gray-400">{m.canonical_state}</div>
                    </td>
                    <td className="p-4 font-bold text-emerald-400">{m.utilisation_pct}%</td>
                    <td className="p-4 font-mono text-gray-200">{m.output_per_rupee} works</td>
                    <td className="p-4 font-mono text-amber-400">{m.avg_sanction_delay_days} days</td>
                    <td className="p-4 font-mono text-purple-300">{m.category_entropy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
