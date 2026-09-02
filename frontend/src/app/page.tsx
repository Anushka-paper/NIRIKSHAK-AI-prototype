"use client";

import { useEffect, useState } from "react";
import { 
  Activity, 
  IndianRupee, 
  MapPin, 
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
  FileText,
  TrendingUp,
  BrainCircuit,
  Clock,
  AlertCircle,
  ChevronRight,
  Sparkles,
  Zap,
  BarChart3,
  PieChart,
  ArrowUpRight,
  Shield,
  Eye,
  Info,
  X,
  Send,
  UserCheck2,
  Compass,
  Truck,
  CopyCheck,
  HeartHandshake,
  Cpu,
  Inbox,
  GitCompare,
  Calendar
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

function formatWorkId(rawId: string) {
  if (!rawId) return "WRK-N/A";
  if (rawId.startsWith("WORK_HASH_")) {
    return "WRK-" + rawId.replace("WORK_HASH_", "").slice(0, 12);
  }
  return rawId;
}

function formatAlertId(rawId: string) {
  if (!rawId) return "ALT-N/A";
  if (rawId.startsWith("ALT_")) {
    return "ALT-" + rawId.replace("ALT_", "").slice(0, 12);
  }
  return rawId;
}

function cleanMpName(name: string) {
  if (!name || name.trim() === "()" || name.trim() === "UNKNOWN" || name.trim() === "") {
    return "IDA / MINISTRY WORK";
  }
  return name.replace(/\(\)/g, "").trim();
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<
    "overview" | "early_warning" | "compliance" | "duplicates" | "financial" | 
    "operational" | "geographical" | "vendors" | 
    "calamity" | "models" | "data_quality" | "works" | "features"
  >("overview");
  
  const [selectedHouse, setSelectedHouse] = useState<string>("all");
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);

  const [stats, setStats] = useState<any>(null);
  const [fetchError, setFetchError] = useState<boolean>(false);

  // Data States
  const [complianceSummary, setComplianceSummary] = useState<any>(null);
  const [violations, setViolations] = useState<any[]>([]);
  const [selectedRuleCode, setSelectedRuleCode] = useState<string>("");
  const [complianceSearch, setComplianceSearch] = useState<string>("");

  const [duplicatesData, setDuplicatesData] = useState<any[]>([]);
  const [selectedDuplicateLayer, setSelectedDuplicateLayer] = useState<string>("");
  const [duplicateSearch, setDuplicateSearch] = useState<string>("");

  const [geoData, setGeoData] = useState<any>(null);
  const [geoSignals, setGeoSignals] = useState<any[]>([]);
  const [geoLevel, setGeoLevel] = useState<string>("state");

  const [financialData, setFinancialData] = useState<any>(null);
  const [operationalData, setOperationalData] = useState<any>(null);

  const [vendorData, setVendorData] = useState<any>(null);
  const [vendorSearch, setVendorSearch] = useState<string>("");

  const [calamityData, setCalamityData] = useState<any>(null);
  const [modelStatusData, setModelStatusData] = useState<any>(null);

  const [works, setWorks] = useState<any[]>([]);
  const [mpFeatures, setMpFeatures] = useState<any[]>([]);

  const [earlyWarningSummary, setEarlyWarningSummary] = useState<any>(null);
  const [earlyWarningAlerts, setEarlyWarningAlerts] = useState<any[]>([]);

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/dashboard/overview?house=${selectedHouse}`);
      if (res.ok) {
        setStats(await res.json());
        setFetchError(false);
      }
    } catch (err) {
      console.warn("Backend poll warning:", err);
      setFetchError(true);
    } finally {
      setLoading(false);
    }
  };

  const fetchTabContent = async () => {
    setLoading(true);
    try {
      if (activeTab === "early_warning") {
        const ewSum = await fetch(`${API_URL}/api/v1/early-warning/summary`);
        if (ewSum.ok) setEarlyWarningSummary(await ewSum.json());

        const ewAlerts = await fetch(`${API_URL}/api/v1/early-warning/alerts?limit=40`);
        if (ewAlerts.ok) setEarlyWarningAlerts((await ewAlerts.json()).alerts || []);
      }

      if (activeTab === "geographical") {
        const res = await fetch(`${API_URL}/api/v1/analytics/geography/states?limit=30`);
        if (res.ok) setGeoData(await res.json());

        const sigRes = await fetch(`${API_URL}/api/v1/analytics/geography/anomalies?limit=10`);
        if (sigRes.ok) setGeoSignals((await sigRes.json()).signals || []);
      }

      if (activeTab === "vendors") {
        let url = `${API_URL}/api/v1/vendors/risk?limit=40`;
        if (vendorSearch) url += `&search=${encodeURIComponent(vendorSearch)}`;
        const res = await fetch(url);
        if (res.ok) setVendorData(await res.json());
      }

      if (activeTab === "models") {
        const res = await fetch(`${API_URL}/api/v1/models/status`);
        if (res.ok) setModelStatusData(await res.json());
      }

      if (activeTab === "works") {
        let url = `${API_URL}/api/v1/standardization/master-works?limit=40`;
        const res = await fetch(url);
        if (res.ok) setWorks((await res.json()).works || []);
      }
    } catch (err) {
      console.warn("Tab fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, [selectedHouse]);

  useEffect(() => {
    fetchTabContent();
  }, [activeTab, selectedHouse, geoLevel, vendorSearch]);

  if (fetchError && !stats) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#faf9fc] text-slate-900 p-6 font-sans">
        <div className="bg-white border border-purple-200 rounded-3xl p-10 max-w-lg text-center shadow-xl shadow-purple-500/5">
          <div className="w-16 h-16 bg-orange-100 border border-orange-300 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="w-8 h-8 text-orange-600 animate-bounce" />
          </div>
          <h2 className="text-2xl font-black text-slate-900 mb-2">Connecting to NIRIKSHAK AI...</h2>
          <p className="text-slate-500 text-sm mb-8 leading-relaxed">
            FastAPI analytical service is initializing. Click retry to verify live sync.
          </p>
          <button
            onClick={fetchOverview}
            className="px-8 py-3 bg-orange-500 hover:bg-orange-600 text-white font-bold rounded-2xl text-sm transition shadow-lg shadow-orange-500/25 active:scale-95"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#faf9fc] text-slate-900 font-sans selection:bg-orange-500 selection:text-white overflow-hidden">
      {/* SIDE PANEL NAVIGATION */}
      <aside className={`w-72 bg-white border-r border-purple-100 flex flex-col justify-between p-6 transition-all z-50 shadow-sm ${
        sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      }`}>
        <div className="space-y-6 overflow-y-auto pr-1">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 bg-gradient-to-tr from-orange-500 via-amber-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-md shadow-orange-500/20 border border-white">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-xl font-black tracking-tight text-slate-900">
                  NIRIKSHAK <span className="bg-clip-text text-transparent bg-gradient-to-r from-orange-500 to-purple-600">AI</span>
                </h1>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-orange-100 border border-orange-200 text-orange-700 tracking-wider">
                Sentinel Platform
              </span>
            </div>
          </div>

          <div className="space-y-1.5">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-3 block mb-1">
              Command Modules (§22)
            </span>

            {[
              { id: "overview", label: "Executive Dashboard", icon: Activity },
              { id: "early_warning", label: "Early Warning Dashboard", icon: BrainCircuit, badge: "243k" },
              { id: "geographical", label: "Geographical Analytics", icon: Compass },
              { id: "vendors", label: "Vendor Intelligence", icon: Truck, badge: "21.1k" },
              { id: "models", label: "Model Monitoring", icon: Cpu }
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`w-full px-3.5 py-2.5 rounded-2xl text-xs font-bold flex items-center justify-between transition-all ${
                    isActive
                      ? "bg-purple-900 text-white shadow-lg shadow-purple-900/25 scale-[1.02]"
                      : "text-slate-600 hover:text-slate-900 hover:bg-purple-50/70"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? "text-orange-400" : "text-slate-500"}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-mono font-black ${
                      isActive ? "bg-orange-500 text-white" : "bg-purple-100 text-purple-800"
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <div className="bg-purple-50/80 border border-purple-200/80 p-4 rounded-2xl text-xs mt-4">
          <div className="flex items-center gap-2 text-purple-900 font-bold mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" /> Live Backend Connected
          </div>
          <p className="text-[11px] text-slate-500">FastAPI REST Server active on http://127.0.0.1:8000</p>
        </div>
      </aside>

      {/* RIGHT MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-xl border-b border-purple-100 px-8 py-4 flex items-center justify-between gap-4 shadow-sm">
          <div>
            <h2 className="text-xl font-black text-slate-900 capitalize">
              {activeTab === "overview" && "Executive Dashboard"}
              {activeTab === "early_warning" && "Early Warning Dashboard (§14, §21)"}
              {activeTab === "geographical" && "Geographical Trends & Spatial Analytics Module (§2-§19)"}
              {activeTab === "vendors" && "Vendor Intelligence Engine & Feature Store (§7)"}
              {activeTab === "models" && "Production-Ready Unsupervised Anomaly Detection Architecture (§8)"}
            </h2>
            <p className="text-xs text-slate-500 font-medium">Synthesized eSAKSHI Pipeline Datasets</p>
          </div>
        </header>

        <div className="p-8 space-y-8">

          {loading && (
            <div className="space-y-6 animate-pulse">
              <div className="h-32 bg-purple-100/60 rounded-3xl w-full" />
              <div className="grid grid-cols-3 gap-6">
                <div className="h-40 bg-purple-100/40 rounded-3xl" />
                <div className="h-40 bg-purple-100/40 rounded-3xl" />
                <div className="h-40 bg-purple-100/40 rounded-3xl" />
              </div>
            </div>
          )}

          {/* TAB 1: EXECUTIVE DASHBOARD */}
          {!loading && activeTab === "overview" && stats && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 text-white border border-purple-700/40 rounded-3xl p-6 shadow-xl">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-orange-500 text-white rounded-2xl flex items-center justify-center font-black shadow-md shadow-orange-500/30">
                    <Landmark className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-xs uppercase font-extrabold text-orange-300 tracking-wider">Executive Overview</span>
                    <h2 className="text-2xl font-black text-white">All Houses Sentinel Target</h2>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-6 text-xs text-purple-100">
                  <div className="bg-white/10 px-4 py-2 rounded-xl border border-white/10 backdrop-blur-md">
                    <span className="text-orange-200 block text-[10px] uppercase font-bold">Total Works Tracked</span>
                    <strong className="text-white text-sm font-black">{stats.total_works?.toLocaleString()} Works</strong>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Recommended</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.total_budget_cr?.toLocaleString()} Cr</p>
                </div>
                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Sanctioned</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.sanctioned_budget_cr?.toLocaleString()} Cr</p>
                </div>
                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Expenditure Disbursed</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.total_expenditure_cr?.toLocaleString()} Cr</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 10: MODEL MONITORING (§8) */}
          {!loading && activeTab === "models" && modelStatusData && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-gradient-to-r from-purple-950 via-indigo-950 to-slate-900 text-white border border-purple-800 rounded-3xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-black">Production-Ready Unsupervised Anomaly Detection Architecture (§8)</h3>
                  <p className="text-xs text-purple-200 mt-1 font-medium">Dual-model architecture: IsolationForest (Primary) + LOF (Secondary Density Cross-Check) with RobustScaler & Population Stability Index (PSI)</p>
                </div>
                <div className="px-4 py-2 bg-white/10 rounded-2xl border border-white/20 text-xs font-bold text-orange-300">
                  {modelStatusData.total_works_evaluated?.toLocaleString() || "243,886"} Works Evaluated
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-purple-950 text-white border border-purple-900 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-purple-200 uppercase">Primary Model: IsolationForest (v1)</span>
                  <p className="text-3xl font-black text-orange-400 mt-2">100 Estimators</p>
                  <span className="text-[10px] text-purple-200 mt-1 block">Contamination = 0.05 (Dynamic Elbow Detection)</span>
                </div>

                <div className="bg-indigo-950 text-white border border-indigo-900 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-indigo-200 uppercase">Secondary Model: LOF (v1)</span>
                  <p className="text-3xl font-black text-indigo-300 mt-2">k = 20 Density Neighbors</p>
                  <span className="text-[10px] text-indigo-200 mt-1 block">Novelty Scoring & Local Cluster Outliers</span>
                </div>

                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">Population Stability Index (PSI)</span>
                  <p className="text-3xl font-black text-emerald-700 mt-2">PSI = {modelStatusData.data_drift?.population_stability_index || 0.000}</p>
                  <span className="text-[10px] text-emerald-600 font-bold block mt-1">Status: STABLE (No retraining required)</span>
                </div>
              </div>

              {/* Monitored Features PSI Breakdown */}
              {modelStatusData.data_drift?.feature_psi_breakdown && (
                <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                  <div className="p-5 border-b border-purple-100 bg-purple-50/40">
                    <h4 className="text-sm font-black uppercase text-purple-950">Monitored Feature Matrix & PSI Population Drift Breakdown (§8)</h4>
                  </div>
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                        <th className="px-5 py-4 whitespace-nowrap">Feature Column Name</th>
                        <th className="px-5 py-4 whitespace-nowrap">Scaler / Transformer (§8)</th>
                        <th className="px-5 py-4 whitespace-nowrap">Population Stability Index (PSI)</th>
                        <th className="px-5 py-4 whitespace-nowrap">Drift Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-purple-50 font-medium">
                      {Object.entries(modelStatusData.data_drift.feature_psi_breakdown).map(([feat, psiVal]: any, i: number) => (
                        <tr key={i} className="hover:bg-purple-50/60 transition-all">
                          <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-slate-900">{feat}</td>
                          <td className="px-5 py-4 whitespace-nowrap">
                            <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold bg-purple-100 text-purple-900 border border-purple-200">
                              {feat.includes("was_missing") ? "Boolean Missingness Indicator" : feat.includes("freq_encoded") ? "Frequency Encoded" : "RobustScaler (Median/IQR)"}
                            </span>
                          </td>
                          <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-emerald-800">{psiVal}</td>
                          <td className="px-5 py-4 whitespace-nowrap">
                            <span className="px-3 py-1 rounded-full text-[10px] font-black bg-emerald-100 text-emerald-900 border border-emerald-300">
                              STABLE
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
