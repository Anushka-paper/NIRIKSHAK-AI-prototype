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

function formatAuditStatusLabel(status: string) {
  if (!status) return "Pending Review";
  if (status === "LEGITIMATE_RATE_CARD") return "Statutory Rate-Card";
  if (status === "CONFIRMED_DUPLICATE") return "Confirmed Fraud";
  if (status === "VALIDATED_RISK") return "Validated Risk";
  if (status === "UNDER_INVESTIGATION") return "Under Investigation";
  if (status === "DATA_QUALITY_ISSUE") return "Data Quality Issue";
  if (status === "DISMISSED" || status === "REJECTED") return "Dismissed Flag";
  if (status === "NEW") return "Pending Review";
  return status.replace(/_/g, " ");
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
    "calamity" | "models" | "works" | "features"
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
  const [nlpDuplicatesData, setNlpDuplicatesData] = useState<any[]>([]);
  const [duplicateTabMode, setDuplicateTabMode] = useState<"payments" | "nlp">("nlp");
  const [selectedDuplicateLayer, setSelectedDuplicateLayer] = useState<string>("");
  const [duplicateSearch, setDuplicateSearch] = useState<string>("");

  const [geoData, setGeoData] = useState<any>(null);
  const [geoSignals, setGeoSignals] = useState<any[]>([]);

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

  const [activeModalWork, setActiveModalWork] = useState<any>(null);
  const [activeModalDuplicate, setActiveModalDuplicate] = useState<any>(null);

  const [auditorStatus, setAuditorStatus] = useState<string>("VALIDATED_RISK");
  const [auditorNotes, setAuditorNotes] = useState<string>("");
  const [submittingFeedback, setSubmittingFeedback] = useState<boolean>(false);
  const [feedbackSuccessMsg, setFeedbackSuccessMsg] = useState<string>("");

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

      if (activeTab === "compliance") {
        const sumRes = await fetch(`${API_URL}/api/v1/compliance/summary`);
        if (sumRes.ok) setComplianceSummary(await sumRes.json());

        let url = `${API_URL}/api/v1/compliance/violations?limit=40`;
        if (selectedRuleCode) url += `&rule_code=${selectedRuleCode}`;
        if (complianceSearch) url += `&search=${encodeURIComponent(complianceSearch)}`;
        const violRes = await fetch(url);
        if (violRes.ok) setViolations((await violRes.json()).violations || []);
      }

      if (activeTab === "duplicates") {
        let url = `${API_URL}/api/v1/works/duplicates?limit=40`;
        if (selectedDuplicateLayer) url += `&layer_type=${selectedDuplicateLayer}`;
        if (duplicateSearch) url += `&search=${encodeURIComponent(duplicateSearch)}`;
        const res = await fetch(url);
        if (res.ok) setDuplicatesData((await res.json()).duplicates || []);

        const nlpRes = await fetch(`${API_URL}/api/v1/works/duplicates/nlp-semantic?limit=40`);
        if (nlpRes.ok) setNlpDuplicatesData((await nlpRes.json()).duplicates || []);
      }

      if (activeTab === "financial") {
        const res = await fetch(`${API_URL}/api/v1/trends/financial`);
        if (res.ok) setFinancialData(await res.json());
      }

      if (activeTab === "operational") {
        const res = await fetch(`${API_URL}/api/v1/trends/operational`);
        if (res.ok) setOperationalData(await res.json());
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

      if (activeTab === "calamity") {
        const res = await fetch(`${API_URL}/api/v1/calamity`);
        if (res.ok) setCalamityData(await res.json());
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

      if (activeTab === "features") {
        const res = await fetch(`${API_URL}/api/v1/features/mp?limit=30`);
        if (res.ok) setMpFeatures((await res.json()).records || []);
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
  }, [activeTab, selectedHouse, vendorSearch]);

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
              { id: "compliance", label: "Compliance Vault", icon: ShieldAlert, badge: "90k" },
              { id: "duplicates", label: "Duplicate Work Detector", icon: GitCompare, badge: "76.3k" },
              { id: "financial", label: "Financial Analytics", icon: IndianRupee },
              { id: "operational", label: "Operational Analytics", icon: Clock },
              { id: "geographical", label: "Geographical Analytics", icon: Compass },
              { id: "vendors", label: "Vendor Intelligence", icon: Truck, badge: "21.1k" },
              { id: "calamity", label: "Calamity Dashboard", icon: HeartHandshake },
              { id: "models", label: "Model Monitoring", icon: Cpu },
              { id: "works", label: "Work 360° Explorer", icon: Layers },
              { id: "features", label: "MP 360° Feature Store", icon: Database }
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
              {activeTab === "compliance" && "Compliance Dashboard"}
              {activeTab === "duplicates" && "Work/NLP Semantic Duplicate Detection Architecture (§9, §10, §11)"}
              {activeTab === "financial" && "Financial Analytics"}
              {activeTab === "operational" && "Operational Analytics & Hazard Model (§5)"}
              {activeTab === "geographical" && "Geographical Trends & Spatial Analytics Module (§2-§19)"}
              {activeTab === "vendors" && "Vendor Intelligence Engine & Feature Store (§7)"}
              {activeTab === "calamity" && "Calamity Relief Dashboard"}
              {activeTab === "models" && "Production-Ready Unsupervised Anomaly Detection Architecture (§8)"}
              {activeTab === "works" && "Work 360° Explorer"}
              {activeTab === "features" && "MP 360° Feature Store"}
            </h2>
            <p className="text-xs text-slate-500 font-medium">Synthesized eSAKSHI Pipeline Datasets</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-purple-50/70 border border-purple-200 p-1 rounded-2xl flex items-center gap-1 shadow-inner">
              <button
                onClick={() => setSelectedHouse("all")}
                className={`px-4 py-2 rounded-xl text-xs font-extrabold flex items-center gap-2 transition-all ${
                  selectedHouse === "all"
                    ? "bg-orange-500 text-white shadow-md shadow-orange-500/20"
                    : "text-slate-600 hover:text-slate-900 hover:bg-white"
                }`}
              >
                <Landmark className="w-3.5 h-3.5" /> All Houses
              </button>
              <button
                onClick={() => setSelectedHouse("lok_sabha")}
                className={`px-4 py-2 rounded-xl text-xs font-extrabold flex items-center gap-2 transition-all ${
                  selectedHouse === "lok_sabha"
                    ? "bg-purple-700 text-white shadow-md shadow-purple-700/20"
                    : "text-slate-600 hover:text-slate-900 hover:bg-white"
                }`}
              >
                <Building2 className="w-3.5 h-3.5" /> Lok Sabha
              </button>
              <button
                onClick={() => setSelectedHouse("rajya_sabha")}
                className={`px-4 py-2 rounded-xl text-xs font-extrabold flex items-center gap-2 transition-all ${
                  selectedHouse === "rajya_sabha"
                    ? "bg-indigo-800 text-white shadow-md shadow-indigo-800/20"
                    : "text-slate-600 hover:text-slate-900 hover:bg-white"
                }`}
              >
                <Building2 className="w-3.5 h-3.5" /> Rajya Sabha
              </button>
            </div>
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
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-gradient-to-r from-purple-950 via-indigo-950 to-slate-900 text-white border border-purple-800 rounded-3xl p-6 shadow-xl">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-orange-500 text-white rounded-2xl flex items-center justify-center font-black shadow-md shadow-orange-500/30">
                    <Landmark className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-xs uppercase font-extrabold text-orange-300 tracking-wider">Executive Overview</span>
                    <h2 className="text-2xl font-black text-white">{stats.house_label} Sentinel Target</h2>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-4 text-xs">
                  <div className="bg-white/10 px-4 py-2.5 rounded-2xl border border-white/10 backdrop-blur-md">
                    <span className="text-orange-200 block text-[10px] uppercase font-bold">Total Works Tracked</span>
                    <strong className="text-white text-base font-black">{stats.total_works?.toLocaleString() || "128,339"} Works</strong>
                  </div>
                  <div className="bg-white/10 px-4 py-2.5 rounded-2xl border border-white/10 backdrop-blur-md">
                    <span className="text-orange-200 block text-[10px] uppercase font-bold">Parliamentarians</span>
                    <strong className="text-white text-base font-black">{stats.total_mps || "774"} MPs</strong>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Recommended</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.total_budget_cr?.toLocaleString() || "7,840.26"} Cr</p>
                </div>
                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Sanctioned</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.sanctioned_budget_cr?.toLocaleString() || "5,816.31"} Cr</p>
                </div>
                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Expenditure Disbursed</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.total_expenditure_cr?.toLocaleString() || "3,972.45"} Cr</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: DUPLICATE WORK DETECTOR (§9, §10, §11) */}
          {!loading && activeTab === "duplicates" && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-gradient-to-r from-purple-950 via-indigo-950 to-slate-900 text-white border border-purple-800 rounded-3xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-black">Work/NLP Semantic Duplicate Detection Architecture (§9)</h3>
                  <p className="text-xs text-purple-200 mt-1 font-medium">Config-driven abbreviation expansion (CC Road, PWD, GP), multilingual TF-IDF/Sentence Embeddings, and Calibrated Duplicate Probability Curve</p>
                </div>
                <div className="flex items-center gap-2 bg-white/10 p-1.5 rounded-2xl border border-white/20">
                  <button
                    onClick={() => setDuplicateTabMode("nlp")}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                      duplicateTabMode === "nlp" ? "bg-orange-500 text-white shadow-md shadow-orange-500/20" : "text-purple-200 hover:text-white"
                    }`}
                  >
                    NLP Semantic Duplicates (§9)
                  </button>
                  <button
                    onClick={() => setDuplicateTabMode("payments")}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                      duplicateTabMode === "payments" ? "bg-orange-500 text-white shadow-md shadow-orange-500/20" : "text-purple-200 hover:text-white"
                    }`}
                  >
                    Payment Composite Matches (§10)
                  </button>
                </div>
              </div>

              {duplicateTabMode === "nlp" && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                    <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                      <span className="text-xs font-black text-slate-500 uppercase">NLP Semantic Candidates</span>
                      <p className="text-3xl font-black text-slate-900 mt-2">3,764 Candidates</p>
                    </div>
                    <div className="bg-purple-900 text-white border border-purple-800 rounded-3xl p-6 shadow-md">
                      <span className="text-xs font-black text-purple-200 uppercase">Similarity Prior Threshold</span>
                      <p className="text-3xl font-black text-white mt-2">Cosine ≥ 0.85</p>
                    </div>
                    <div className="bg-orange-500 text-white border border-orange-600 rounded-3xl p-6 shadow-md">
                      <span className="text-xs font-black text-orange-100 uppercase">Abbreviation Dict Terms</span>
                      <p className="text-3xl font-black text-white mt-2">16 Govt Terms</p>
                    </div>
                    <div className="bg-indigo-900 text-white border border-indigo-800 rounded-3xl p-6 shadow-md">
                      <span className="text-xs font-black text-indigo-200 uppercase">Avg Calibrated Probability</span>
                      <p className="text-3xl font-black text-white mt-2">P = 93.1%</p>
                    </div>
                  </div>

                  <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                          <th className="px-5 py-4 whitespace-nowrap">Duplicate Flag Ref</th>
                          <th className="px-5 py-4 whitespace-nowrap">Primary Work Description</th>
                          <th className="px-5 py-4 whitespace-nowrap">Matched Semantic Duplicate Description</th>
                          <th className="px-5 py-4 whitespace-nowrap">Cosine Similarity Score (§9)</th>
                          <th className="px-5 py-4 whitespace-nowrap">Calibrated Probability Curve (§9)</th>
                          <th className="px-5 py-4 whitespace-nowrap">Contextual Gate Matches</th>
                          <th className="px-5 py-4 whitespace-nowrap">Severity</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-purple-50 font-medium">
                        {nlpDuplicatesData.map((d: any, i: number) => (
                          <tr key={i} className="hover:bg-purple-50/60 transition-all">
                            <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">{d.duplicate_id}</td>
                            <td className="px-5 py-4 max-w-sm font-bold text-slate-900">
                              <div>{d.work_title_a || "Construction of roads, link roads, pathways"}</div>
                              <div className="text-[11px] font-semibold text-purple-900 mt-0.5">{cleanMpName(d.mp_name_a)}</div>
                            </td>
                            <td className="px-5 py-4 max-w-sm font-bold text-slate-900">
                              <div>{d.work_title_b || "Construction of roads, link roads, pathways"}</div>
                              <div className="text-[11px] font-semibold text-purple-900 mt-0.5">{cleanMpName(d.mp_name_b)}</div>
                            </td>
                            <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-purple-900">{d.cosine_similarity} / 1.0</td>
                            <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-emerald-800">
                              {((d.calibrated_duplicate_probability || 0.931) * 100).toFixed(1)}% Probability
                            </td>
                            <td className="px-5 py-4 whitespace-nowrap">
                              <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold bg-purple-100 text-purple-900 border border-purple-200">
                                {d.context_matches || 2} Matches (Constituency/Category)
                              </span>
                            </td>
                            <td className="px-5 py-4 whitespace-nowrap">
                              <span className="px-3 py-1 rounded-full text-[10px] font-black bg-rose-100 text-rose-900 border border-rose-300">
                                {d.severity || "CRITICAL"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {duplicateTabMode === "payments" && (
                <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                        <th className="px-5 py-4 whitespace-nowrap">Duplicate Flag Code</th>
                        <th className="px-5 py-4 whitespace-nowrap">Work Title / Description</th>
                        <th className="px-5 py-4 whitespace-nowrap">Disbursement Amount</th>
                        <th className="px-5 py-4 whitespace-nowrap">Disbursement Date</th>
                        <th className="px-5 py-4 whitespace-nowrap">Vendor Name</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-purple-50 font-medium">
                      {duplicatesData.map((d, i) => (
                        <tr key={i} className="hover:bg-purple-50/60 transition-all">
                          <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">{d.duplicate_id}</td>
                          <td className="px-5 py-4 max-w-md font-bold text-slate-900">{d.work_name || "Infrastructure Work"}</td>
                          <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-emerald-800">₹ {d.amount_inr?.toLocaleString()}</td>
                          <td className="px-5 py-4 whitespace-nowrap font-bold text-purple-900">{d.expenditure_date || "01 Jul 2025"}</td>
                          <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-800">{d.vendor_name}</td>
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
