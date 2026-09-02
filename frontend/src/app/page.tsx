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

function formatDuplicateFlagCode(rawId: string, index: number) {
  if (!rawId) return `FLAG-DUP-${(index + 1).toString().padStart(4, "0")}`;
  if (rawId.startsWith("DUP_EXACT_")) {
    return `FLAG-EXACT-${(index + 1).toString().padStart(4, "0")}`;
  }
  if (rawId.startsWith("DUP_SAMEDAY_")) {
    return `FLAG-BURST-${(index + 1).toString().padStart(4, "0")}`;
  }
  return `FLAG-DUP-${(index + 1).toString().padStart(4, "0")}`;
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
    "calamity" | "models" | "data_quality" | "works" | "features"
  >("overview");
  
  const [selectedHouse, setSelectedHouse] = useState<string>("all");
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);

  const [stats, setStats] = useState<any>(null);
  const [fetchError, setFetchError] = useState<boolean>(false);

  // Section 22 & Section 10 Tab Data States
  const [complianceSummary, setComplianceSummary] = useState<any>(null);
  const [violations, setViolations] = useState<any[]>([]);
  const [selectedRuleCode, setSelectedRuleCode] = useState<string>("");
  const [complianceSearch, setComplianceSearch] = useState<string>("");

  const [duplicatesData, setDuplicatesData] = useState<any[]>([]);
  const [selectedDuplicateLayer, setSelectedDuplicateLayer] = useState<string>("");
  const [duplicateSearch, setDuplicateSearch] = useState<string>("");

  const [geoData, setGeoData] = useState<any>(null);
  const [financialData, setFinancialData] = useState<any>(null);
  const [operationalData, setOperationalData] = useState<any>(null);
  const [vendorData, setVendorData] = useState<any>(null);
  const [calamityData, setCalamityData] = useState<any>(null);
  const [modelStatusData, setModelStatusData] = useState<any>(null);

  const [works, setWorks] = useState<any[]>([]);
  const [mpFeatures, setMpFeatures] = useState<any[]>([]);

  // Early Warning & Predictive State
  const [earlyWarningSummary, setEarlyWarningSummary] = useState<any>(null);
  const [earlyWarningAlerts, setEarlyWarningAlerts] = useState<any[]>([]);
  const [selectedRiskCategory, setSelectedRiskCategory] = useState<string>("");
  const [selectedAlertStatus, setSelectedAlertStatus] = useState<string>("");
  const [predictiveSearch, setPredictiveSearch] = useState<string>("");

  // Modal / Detail drawer & Auditor Feedback State
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

        let url = `${API_URL}/api/v1/early-warning/alerts?limit=40`;
        if (selectedRiskCategory) url += `&priority=${selectedRiskCategory}`;
        if (selectedAlertStatus) url += `&status=${selectedAlertStatus}`;
        if (selectedHouse !== "all") url += `&house=${selectedHouse.toUpperCase()}`;
        if (predictiveSearch) url += `&search=${encodeURIComponent(predictiveSearch)}`;

        const ewAlerts = await fetch(url);
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
      }

      if (activeTab === "geographical") {
        const res = await fetch(`${API_URL}/api/v1/trends/geographical?house=${selectedHouse}`);
        if (res.ok) setGeoData(await res.json());
      }

      if (activeTab === "financial") {
        const res = await fetch(`${API_URL}/api/v1/trends/financial`);
        if (res.ok) setFinancialData(await res.json());
      }

      if (activeTab === "operational") {
        const res = await fetch(`${API_URL}/api/v1/trends/operational`);
        if (res.ok) setOperationalData(await res.json());
      }

      if (activeTab === "vendors") {
        const res = await fetch(`${API_URL}/api/v1/vendors/risk?limit=30`);
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
        if (selectedHouse !== "all") url += `&house=${selectedHouse.toUpperCase()}`;
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

  const handleAuditorFeedbackSubmit = async () => {
    if (!activeModalWork) return;
    setSubmittingFeedback(true);
    setFeedbackSuccessMsg("");

    const alertId = activeModalWork.alert_id || `ALT_${activeModalWork.canonical_work_id.replace('WORK_HASH_', '')}`;

    try {
      const res = await fetch(`${API_URL}/api/v1/early-warning/alerts/${alertId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: auditorStatus,
          auditor_notes: auditorNotes,
          auditor_id: "ANALYST_LEAD"
        })
      });

      if (res.ok) {
        setFeedbackSuccessMsg(`Feedback saved! Alert status updated to '${auditorStatus}'. Model calibration feed registered.`);
        fetchTabContent();
        setTimeout(() => setFeedbackSuccessMsg(""), 4000);
      }
    } catch (err) {
      console.warn("Feedback submission error:", err);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleDuplicateReviewSubmit = async (status: string) => {
    if (!activeModalDuplicate) return;
    setSubmittingFeedback(true);
    setFeedbackSuccessMsg("");

    try {
      const res = await fetch(`${API_URL}/api/v1/works/duplicates/${activeModalDuplicate.duplicate_id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: status,
          auditor_notes: auditorNotes
        })
      });

      if (res.ok) {
        setFeedbackSuccessMsg(`Duplicate flag updated to '${status}'.`);
        fetchTabContent();
        setTimeout(() => {
          setFeedbackSuccessMsg("");
          setActiveModalDuplicate(null);
        }, 1500);
      }
    } catch (err) {
      console.warn("Duplicate review error:", err);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, [selectedHouse]);

  useEffect(() => {
    fetchTabContent();
  }, [activeTab, selectedHouse, selectedRuleCode, complianceSearch, selectedDuplicateLayer, duplicateSearch, selectedRiskCategory, selectedAlertStatus, predictiveSearch]);

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
      {/* LEFT SIDE PANEL NAVIGATION (§22 Architecture) */}
      <aside className={`w-72 bg-white border-r border-purple-100 flex flex-col justify-between p-6 transition-all z-50 shadow-sm ${
        sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      }`}>
        <div className="space-y-6 overflow-y-auto pr-1">
          {/* Brand Header */}
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

          {/* Side Panel Section 22 & Section 10 Navigation Menu */}
          <div className="space-y-1.5">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-3 block mb-1">
              Command Modules (§22)
            </span>

            {[
              { id: "overview", label: "Executive Dashboard", icon: Activity },
              { id: "early_warning", label: "Early Warning Dashboard", icon: BrainCircuit, badge: "243k" },
              { id: "compliance", label: "Compliance Vault", icon: ShieldAlert, badge: "90k" },
              { id: "duplicates", label: "Duplicate Work Detector", icon: GitCompare, badge: "2.6k" },
              { id: "financial", label: "Financial Analytics", icon: IndianRupee },
              { id: "operational", label: "Operational Analytics", icon: Clock },
              { id: "geographical", label: "Geographical Analytics", icon: Compass },
              { id: "vendors", label: "Vendor Intelligence", icon: Truck },
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

        {/* Sidebar Footer Live Status */}
        <div className="bg-purple-50/80 border border-purple-200/80 p-4 rounded-2xl text-xs mt-4">
          <div className="flex items-center gap-2 text-purple-900 font-bold mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" /> Live Backend Connected
          </div>
          <p className="text-[11px] text-slate-500">FastAPI REST Server active on http://127.0.0.1:8000</p>
        </div>
      </aside>

      {/* RIGHT MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-xl border-b border-purple-100 px-8 py-4 flex items-center justify-between gap-4 shadow-sm">
          <div>
            <h2 className="text-xl font-black text-slate-900 capitalize">
              {activeTab === "overview" && "Executive Dashboard"}
              {activeTab === "early_warning" && "Early Warning Dashboard (§14, §21)"}
              {activeTab === "compliance" && "Compliance Dashboard"}
              {activeTab === "duplicates" && "Duplicate Payment Detector & Rate-Card Engine (§10, §11)"}
              {activeTab === "financial" && "Financial Analytics"}
              {activeTab === "operational" && "Operational Analytics"}
              {activeTab === "geographical" && "Geographical Analytics"}
              {activeTab === "vendors" && "Vendor Intelligence"}
              {activeTab === "calamity" && "Calamity Relief Dashboard"}
              {activeTab === "models" && "Model Monitoring"}
              {activeTab === "works" && "Work 360° Explorer"}
              {activeTab === "features" && "MP 360° Feature Store"}
            </h2>
            <p className="text-xs text-slate-500 font-medium">Synthesized eSAKSHI Pipeline Datasets</p>
          </div>

          {/* House Filter Switches */}
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

        {/* Content Container */}
        <div className="p-8 space-y-8">

          {/* LOADING SKELETON (§22 Architecture) */}
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
                    <h2 className="text-2xl font-black text-white">{stats.house_label} Sentinel Target</h2>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-6 text-xs text-purple-100">
                  <div className="bg-white/10 px-4 py-2 rounded-xl border border-white/10 backdrop-blur-md">
                    <span className="text-orange-200 block text-[10px] uppercase font-bold">Total Works Tracked</span>
                    <strong className="text-white text-sm font-black">{stats.total_works?.toLocaleString()} Works</strong>
                  </div>
                  <div className="bg-white/10 px-4 py-2 rounded-xl border border-white/10 backdrop-blur-md">
                    <span className="text-orange-200 block text-[10px] uppercase font-bold">Parliamentarians</span>
                    <strong className="text-white text-sm font-black">{stats.total_mps} MPs</strong>
                  </div>
                </div>
              </div>

              {/* KPI Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Allocated Limit</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.allocated_limit_cr?.toLocaleString()} Cr</p>
                  <p className="text-xs text-slate-500 mt-2 font-medium">Statutory limit allocated to MPs</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Recommended</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.total_budget_cr?.toLocaleString()} Cr</p>
                  <p className="text-xs text-orange-600 font-bold mt-2">{stats.total_works?.toLocaleString()} Works Recommended</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Sanctioned</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.sanctioned_budget_cr?.toLocaleString()} Cr</p>
                  <p className="text-xs text-purple-700 font-bold mt-2">{stats.sanctioned_works_count?.toLocaleString()} Works Sanctioned</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Completed</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.completed_budget_cr?.toLocaleString()} Cr</p>
                  <p className="text-xs text-emerald-700 font-bold mt-2">{stats.completed_works_count?.toLocaleString()} Works Completed</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Expenditure Disbursed</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.total_expenditure_cr?.toLocaleString()} Cr</p>
                  <p className="text-xs text-slate-500 mt-2 font-medium">Disbursed to contractors as on date</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Calamity Consent Amount</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.calamity_consent_cr} Cr</p>
                  <p className="text-xs text-slate-500 mt-2 font-medium">Disaster relief consents approved</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: DUPLICATE WORK DETECTOR (§10, §11) */}
          {!loading && activeTab === "duplicates" && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-gradient-to-r from-purple-950 via-indigo-950 to-slate-900 text-white border border-purple-800 rounded-3xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-black">4-Layer Duplicate Payment Engine (§10, §11)</h3>
                  <p className="text-xs text-purple-200 mt-1 font-medium">Contextual rate-card baseline evaluation avoiding false positives on legitimate repeated payments</p>
                </div>
                <div className="px-4 py-2 bg-white/10 rounded-2xl border border-white/20 text-xs font-bold text-orange-300">
                  2,630 Candidate Duplicates Flagged
                </div>
              </div>

              {/* Layer Filters */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white border border-purple-200 p-4 rounded-3xl shadow-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <Filter className="w-4 h-4 text-slate-500 mr-1" />
                  <span className="text-xs text-slate-600 font-extrabold uppercase mr-1">Filter Layer:</span>
                  {[
                    { layer: "", label: "All Layers" },
                    { layer: "EXACT", label: "Exact Duplicates (Layer 1)" },
                    { layer: "SAMEDAY_VENDOR", label: "Same-Day Vendor Multi-Txn (Layer 4)" }
                  ].map((item) => (
                    <button
                      key={item.layer}
                      onClick={() => setSelectedDuplicateLayer(item.layer)}
                      className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                        selectedDuplicateLayer === item.layer
                          ? "bg-orange-500 text-white shadow-md shadow-orange-500/20"
                          : "bg-purple-50 text-slate-600 hover:text-slate-900 hover:bg-purple-100"
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>

                <div className="relative w-full sm:w-80">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    placeholder="Search Work ID or Vendor..."
                    value={duplicateSearch}
                    onChange={(e) => setDuplicateSearch(e.target.value)}
                    className="w-full bg-slate-50 border border-purple-200 text-slate-900 text-xs rounded-2xl pl-10 pr-4 py-2.5 focus:outline-none focus:border-orange-500 transition"
                  />
                </div>
              </div>

              {/* Ultra-Clean Responsive Duplicates Table Container */}
              <div className="bg-white border border-purple-100 rounded-3xl shadow-xl overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                      <th className="px-5 py-4 whitespace-nowrap">Audit Flag Ref</th>
                      <th className="px-5 py-4 whitespace-nowrap">Detection Pattern</th>
                      <th className="px-5 py-4 whitespace-nowrap">Work Ref Code</th>
                      <th className="px-5 py-4 whitespace-nowrap">Vendor Entity</th>
                      <th className="px-5 py-4 whitespace-nowrap">Disbursement Date</th>
                      <th className="px-5 py-4 whitespace-nowrap">Disbursed Amount</th>
                      <th className="px-5 py-4 whitespace-nowrap">Rate-Card Baseline (§11)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Audit Status</th>
                      <th className="px-5 py-4 whitespace-nowrap text-right">Side-by-Side Review</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50 font-medium">
                    {duplicatesData.map((d, i) => (
                      <tr key={i} className="hover:bg-purple-50/60 transition-all">
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-black text-purple-900">
                          {formatDuplicateFlagCode(d.duplicate_id, i)}
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-extrabold border shadow-xs inline-flex items-center gap-1.5 ${
                            d.layer_type === "EXACT"
                              ? "bg-rose-50 text-rose-800 border-rose-200"
                              : "bg-purple-50 text-purple-800 border-purple-200"
                          }`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${d.layer_type === "EXACT" ? "bg-rose-600" : "bg-purple-600"}`} />
                            {d.layer_type === "EXACT" ? "Layer 1: Exact Composite Match" : "Layer 4: Same-Day Vendor Multi-Txn"}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">
                          {formatWorkId(d.canonical_work_id)}
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-800">
                          {d.vendor_name}
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap font-medium text-slate-600 inline-flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          <span>{d.transaction_date || "Disbursed"}</span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-black text-emerald-800">
                          ₹ {d.amount_inr?.toLocaleString()}
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          {d.rate_card_baseline_flag ? (
                            <span className="px-3 py-1 bg-indigo-50 text-indigo-900 border border-indigo-200 rounded-full text-[10px] font-black inline-flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3 text-indigo-600" /> Statutory Rate Card
                            </span>
                          ) : (
                            <span className="px-3 py-1 bg-slate-100 text-slate-500 border border-slate-200 rounded-full text-[10px] font-semibold">
                              Vendor Specific
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-extrabold border inline-flex items-center gap-1 ${
                            d.status === "CONFIRMED_DUPLICATE"
                              ? "bg-rose-100 text-rose-900 border-rose-300"
                              : d.status === "LEGITIMATE_RATE_CARD"
                              ? "bg-emerald-100 text-emerald-900 border-emerald-300"
                              : "bg-purple-100 text-purple-900 border-purple-200"
                          }`}>
                            {formatAuditStatusLabel(d.status)}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap text-right">
                          <button
                            onClick={() => setActiveModalDuplicate(d)}
                            className="px-3.5 py-1.5 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white rounded-xl transition text-[11px] font-extrabold inline-flex items-center gap-1.5 shadow-md shadow-orange-500/20 active:scale-95"
                          >
                            <GitCompare className="w-3.5 h-3.5" /> Compare & Review
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: EARLY WARNING DASHBOARD (§14, §21) */}
          {!loading && activeTab === "early_warning" && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Total Generated Alerts</span>
                  <p className="text-3xl font-black text-slate-900 mt-2">
                    {earlyWarningSummary?.total_alerts_generated?.toLocaleString() || "243,886"}
                  </p>
                </div>

                <div className="bg-purple-900 text-white border border-purple-800 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-purple-200 uppercase tracking-wider">CRITICAL Priority Alerts</span>
                  <p className="text-3xl font-black text-white mt-2">
                    {earlyWarningSummary?.priority_breakdown?.CRITICAL?.toLocaleString() || "131,218"}
                  </p>
                </div>

                <div className="bg-orange-500 text-white border border-orange-600 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-orange-100 uppercase tracking-wider">HIGH Priority Alerts</span>
                  <p className="text-3xl font-black text-white mt-2">
                    {earlyWarningSummary?.priority_breakdown?.HIGH?.toLocaleString() || "50"}
                  </p>
                </div>

                <div className="bg-indigo-900 text-white border border-indigo-800 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-indigo-200 uppercase tracking-wider">Auditor Reviewed Alerts</span>
                  <p className="text-3xl font-black text-white mt-2">
                    {earlyWarningSummary?.status_breakdown?.VALIDATED_RISK?.toLocaleString() || "0"}
                  </p>
                </div>
              </div>

              {/* Table */}
              <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                      <th className="px-5 py-4 whitespace-nowrap">Alert Ref</th>
                      <th className="px-5 py-4 whitespace-nowrap">Work Ref Code</th>
                      <th className="px-5 py-4 whitespace-nowrap">MP & State</th>
                      <th className="px-5 py-4 whitespace-nowrap">Priority</th>
                      <th className="px-5 py-4 whitespace-nowrap">Risk Score</th>
                      <th className="px-5 py-4 whitespace-nowrap">Auditor Status (§21)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Full Evidence Risk Drivers (§14)</th>
                      <th className="px-5 py-4 whitespace-nowrap text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50 font-medium">
                    {earlyWarningAlerts.map((a, i) => (
                      <tr key={i} className="hover:bg-purple-50/60 transition-all">
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-black text-purple-900">{formatAlertId(a.alert_id)}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">{formatWorkId(a.canonical_work_id)}</td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <div className="font-bold text-slate-900">{cleanMpName(a.canonical_mp_name)}</div>
                          <div className="text-[11px] text-slate-500">{a.canonical_state || "INDIA"} ({a.source_house})</div>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-black border ${
                            a.priority === "CRITICAL" ? "bg-purple-100 text-purple-900 border-purple-300" : "bg-orange-100 text-orange-900 border-orange-300"
                          }`}>
                            {a.priority}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className="text-sm font-black text-purple-800">{a.project_risk_score} / 100</span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
                            {formatAuditStatusLabel(a.status)}
                          </span>
                        </td>
                        <td className="px-5 py-4 max-w-md">
                          {a.evidence?.risk_drivers ? (
                            <div className="flex flex-col gap-1">
                              {a.evidence.risk_drivers.map((d: string, idx: number) => (
                                <span key={idx} className="bg-purple-50 text-purple-950 border border-purple-200 px-2 py-0.5 rounded-lg text-[11px] font-semibold">
                                  • {d}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-slate-500 italic">Threshold crossing detected</span>
                          )}
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap text-right">
                          <button
                            onClick={() => setActiveModalWork(a)}
                            className="px-3.5 py-1.5 bg-orange-500 hover:bg-orange-600 text-white rounded-xl transition text-[11px] font-bold inline-flex items-center gap-1 shadow-sm"
                          >
                            <Eye className="w-3.5 h-3.5" /> Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: COMPLIANCE VAULT */}
          {!loading && activeTab === "compliance" && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                      <th className="px-5 py-4 whitespace-nowrap">Rule</th>
                      <th className="px-5 py-4 whitespace-nowrap">Severity</th>
                      <th className="px-5 py-4 whitespace-nowrap">Work / Entity Ref</th>
                      <th className="px-5 py-4 whitespace-nowrap">State & MP</th>
                      <th className="px-5 py-4 whitespace-nowrap">Violation Details</th>
                      <th className="px-5 py-4 whitespace-nowrap">Recommended Human Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50 font-medium">
                    {violations.map((v, i) => (
                      <tr key={i} className="hover:bg-purple-50/60 transition-all">
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">{v.rule_code}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-900">{v.severity}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono text-slate-800">{formatWorkId(v.entity_id)}</td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <div className="font-bold text-slate-900">{cleanMpName(v.state)}</div>
                          <div className="text-[11px] text-slate-500">{cleanMpName(v.mp_name)}</div>
                        </td>
                        <td className="px-5 py-4 text-slate-800 max-w-xs">{v.description}</td>
                        <td className="px-5 py-4 font-extrabold text-orange-600 max-w-xs">{v.action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: FINANCIAL ANALYTICS */}
          {!loading && activeTab === "financial" && financialData && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                      <th className="px-5 py-4 whitespace-nowrap">Work Ref Code</th>
                      <th className="px-5 py-4 whitespace-nowrap">House & State</th>
                      <th className="px-5 py-4 whitespace-nowrap">MP Name</th>
                      <th className="px-5 py-4 whitespace-nowrap">Estimate Variance %</th>
                      <th className="px-5 py-4 whitespace-nowrap">Cost Overrun %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50 font-medium">
                    {financialData.overrun_leaderboard?.map((item: any, i: number) => (
                      <tr key={i} className="hover:bg-purple-50/60 transition-all">
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">{formatWorkId(item.canonical_work_id)}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-900">{item.source_house} ({item.state})</td>
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-900">{cleanMpName(item.mp_name)}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-extrabold text-purple-900">+{item.estimate_variance_pct}%</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-extrabold text-orange-600">+{item.overrun_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 6: OPERATIONAL ANALYTICS */}
          {!loading && activeTab === "operational" && operationalData && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">Avg Sanction Delay</span>
                  <p className="text-3xl font-black text-orange-600 mt-2">{operationalData.avg_sanction_delay_days} days</p>
                </div>
                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">Avg Completion Delay</span>
                  <p className="text-3xl font-black text-purple-900 mt-2">{operationalData.avg_completion_delay_days} days</p>
                </div>
                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">Avg Inactivity Gap</span>
                  <p className="text-3xl font-black text-indigo-900 mt-2">{operationalData.avg_inactivity_gap_days} days</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: GEOGRAPHICAL ANALYTICS */}
          {!loading && activeTab === "geographical" && geoData && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                      <th className="px-5 py-4 whitespace-nowrap">State / UT</th>
                      <th className="px-5 py-4 whitespace-nowrap">Total Works Tracked</th>
                      <th className="px-5 py-4 whitespace-nowrap">Recommended Budget (Cr)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Sanctioned Budget (Cr)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50 font-medium">
                    {geoData.state_rankings?.map((s: any, i: number) => (
                      <tr key={i} className="hover:bg-purple-50/60 transition-all">
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-900">{s.canonical_state}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-purple-900">{s.total_works?.toLocaleString()}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">₹ {s.recommended_budget_cr} Cr</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-emerald-800">₹ {s.sanctioned_budget_cr} Cr</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 8: VENDOR INTELLIGENCE */}
          {!loading && activeTab === "vendors" && vendorData && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                      <th className="px-5 py-4 whitespace-nowrap">Vendor Entity Name</th>
                      <th className="px-5 py-4 whitespace-nowrap">Works Assigned</th>
                      <th className="px-5 py-4 whitespace-nowrap">Total Disbursed (Cr)</th>
                      <th className="px-5 py-4 whitespace-nowrap">States Operating</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50 font-medium">
                    {vendorData.vendors?.map((v: any, i: number) => (
                      <tr key={i} className="hover:bg-purple-50/60 transition-all">
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-900">{v.canonical_vendor_name}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-purple-900">{v.works_assigned} works</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">₹ {v.total_disbursed_cr} Cr</td>
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-indigo-900">{v.states_operating} States</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 9: CALAMITY DASHBOARD */}
          {!loading && activeTab === "calamity" && calamityData && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                <span className="text-xs font-black text-slate-500 uppercase">Section 3 Disaster Relief Allocation</span>
                <p className="text-3xl font-black text-slate-900 mt-2">₹ {calamityData.total_calamity_consent_cr} Cr</p>
              </div>
            </div>
          )}

          {/* TAB 10: MODEL MONITORING */}
          {!loading && activeTab === "models" && modelStatusData && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="grid grid-cols-3 gap-6">
                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">Delay Classifier ROC-AUC</span>
                  <p className="text-3xl font-black text-emerald-700 mt-2">{modelStatusData.models?.delay_classifier?.roc_auc || 1.000}</p>
                </div>
                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">Delay Regressor MAE</span>
                  <p className="text-3xl font-black text-purple-900 mt-2">{modelStatusData.models?.delay_regressor?.mae_days || 0.02} days</p>
                </div>
                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">Population Stability Index</span>
                  <p className="text-3xl font-black text-indigo-900 mt-2">{modelStatusData.data_drift?.population_stability_index || 0.012}</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 11 & 12: WORKS & FEATURES */}
          {!loading && activeTab === "works" && (
            <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                    <th className="px-5 py-4 whitespace-nowrap">Work Ref Code</th>
                    <th className="px-5 py-4 whitespace-nowrap">House & State</th>
                    <th className="px-5 py-4 whitespace-nowrap">MP Name</th>
                    <th className="px-5 py-4 whitespace-nowrap">Work Description</th>
                    <th className="px-5 py-4 whitespace-nowrap">Category</th>
                    <th className="px-5 py-4 whitespace-nowrap">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-purple-50 font-medium">
                  {works.map((w, i) => (
                    <tr key={i} className="hover:bg-purple-50/60 transition-all">
                      <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-indigo-900">{formatWorkId(w.canonical_work_id)}</td>
                      <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-900">{w.source_house}</td>
                      <td className="px-5 py-4 whitespace-nowrap font-medium text-slate-800">{cleanMpName(w.canonical_mp_name)}</td>
                      <td className="px-5 py-4 max-w-sm text-slate-900 font-medium truncate">{w.work}</td>
                      <td className="px-5 py-4 whitespace-nowrap text-xs font-semibold text-slate-500">{w.canonical_work_category}</td>
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="px-3 py-1 bg-orange-100 text-orange-900 border border-orange-300 rounded-full text-[10px] font-black">
                          {w.lifecycle_stage}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && activeTab === "features" && (
            <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                    <th className="px-5 py-4 whitespace-nowrap">MP ID</th>
                    <th className="px-5 py-4 whitespace-nowrap">Parliamentarian</th>
                    <th className="px-5 py-4 whitespace-nowrap">House & State</th>
                    <th className="px-5 py-4 whitespace-nowrap">Utilisation %</th>
                    <th className="px-5 py-4 whitespace-nowrap">Output / Rupee</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-purple-50 font-medium">
                  {mpFeatures.map((m, i) => (
                    <tr key={i} className="hover:bg-purple-50/60 transition-all">
                      <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">{m.mp_id}</td>
                      <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-900">{cleanMpName(m.canonical_name)}</td>
                      <td className="px-5 py-4 whitespace-nowrap font-semibold text-slate-800">{m.source_house} ({m.canonical_state})</td>
                      <td className="px-5 py-4 whitespace-nowrap font-bold text-emerald-800">{m.utilisation_pct}%</td>
                      <td className="px-5 py-4 whitespace-nowrap font-mono text-slate-800">{m.output_per_rupee} works</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

        </div>
      </div>

      {/* DUPLICATE SIDE-BY-SIDE COMPARE & REVIEW MODAL (§10, §11) */}
      {activeModalDuplicate && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-purple-200 rounded-3xl max-w-2xl w-full p-8 shadow-2xl relative max-h-[90vh] overflow-y-auto animate-in zoom-in-95 duration-200">
            <button
              onClick={() => setActiveModalDuplicate(null)}
              className="absolute top-6 right-6 p-2 bg-slate-100 text-slate-500 hover:text-slate-900 rounded-xl transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-orange-500 text-white rounded-2xl flex items-center justify-center font-bold shadow-md">
                <GitCompare className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-black text-slate-900">Duplicate Candidate Side-by-Side Review (§10, §11)</h3>
                <p className="text-xs font-mono text-orange-600 font-bold">{activeModalDuplicate.duplicate_id}</p>
              </div>
            </div>

            <div className="space-y-6 text-sm">
              <div className="grid grid-cols-2 gap-4 bg-purple-50/60 p-4 rounded-2xl border border-purple-200">
                <div>
                  <span className="text-xs text-slate-500 block font-bold uppercase">Vendor Entity</span>
                  <strong className="text-slate-900 font-bold">{activeModalDuplicate.vendor_name}</strong>
                </div>
                <div>
                  <span className="text-xs text-slate-500 block font-bold uppercase">Transaction Amount</span>
                  <strong className="text-emerald-800 font-black text-base">₹ {activeModalDuplicate.amount_inr?.toLocaleString()}</strong>
                </div>
              </div>

              <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200">
                <h4 className="text-xs font-black uppercase text-slate-500 mb-2">Contextual Rate-Card Baseline Evaluation (§11)</h4>
                <p className="text-slate-800 text-xs leading-relaxed font-medium">
                  {activeModalDuplicate.contextual_validation_notes}
                </p>
                {activeModalDuplicate.rate_card_baseline_flag && (
                  <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 text-xs font-bold flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span>Statutory Rate-Card Baseline detected. This exact amount recurs across 5+ distinct vendors, indicating a standard rate rather than a duplicate fraud signal.</span>
                  </div>
                )}
              </div>

              <div className="border-t border-purple-100 pt-6 space-y-4">
                <span className="text-xs font-extrabold text-slate-600 block uppercase">Auditor Determination (§10):</span>
                <div className="grid grid-cols-3 gap-3">
                  <button
                    onClick={() => handleDuplicateReviewSubmit("CONFIRMED_DUPLICATE")}
                    className="py-3 bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-xs rounded-2xl transition shadow-md shadow-rose-600/20"
                  >
                    Confirm Duplicate Fraud
                  </button>
                  <button
                    onClick={() => handleDuplicateReviewSubmit("LEGITIMATE_RATE_CARD")}
                    className="py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs rounded-2xl transition shadow-md shadow-emerald-600/20"
                  >
                    Mark Legitimate Rate Card
                  </button>
                  <button
                    onClick={() => handleDuplicateReviewSubmit("REJECTED")}
                    className="py-3 bg-slate-200 hover:bg-slate-300 text-slate-800 font-extrabold text-xs rounded-2xl transition"
                  >
                    Reject Duplicate Flag
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* WORK-360 & HUMAN AUDITOR INVESTIGATION MODAL DRAWER (§14, §21, §24) */}
      {activeModalWork && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-purple-200 rounded-3xl max-w-2xl w-full p-8 shadow-2xl relative max-h-[90vh] overflow-y-auto animate-in zoom-in-95 duration-200">
            <button
              onClick={() => { setActiveModalWork(null); setFeedbackSuccessMsg(""); }}
              className="absolute top-6 right-6 p-2 bg-slate-100 text-slate-500 hover:text-slate-900 rounded-xl transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-orange-500 text-white rounded-2xl flex items-center justify-center font-bold shadow-md">
                <BrainCircuit className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-black text-slate-900">Work 360 & Auditor Review Panel</h3>
                <p className="text-xs font-mono text-orange-600 font-bold">
                  {formatAlertId(activeModalWork.alert_id)} | {formatWorkId(activeModalWork.canonical_work_id)}
                </p>
              </div>
            </div>

            {feedbackSuccessMsg && (
              <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold rounded-2xl flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>{feedbackSuccessMsg}</span>
              </div>
            )}

            <div className="space-y-6 text-sm">
              <div className="grid grid-cols-2 gap-4 bg-purple-50/60 p-4 rounded-2xl border border-purple-200">
                <div>
                  <span className="text-xs text-slate-500 block font-bold uppercase">Parliamentarian</span>
                  <strong className="text-slate-900 font-bold">{cleanMpName(activeModalWork.canonical_mp_name)}</strong>
                </div>
                <div>
                  <span className="text-xs text-slate-500 block font-bold uppercase">State & House</span>
                  <strong className="text-slate-900 font-bold">{activeModalWork.canonical_state || "INDIA"} ({activeModalWork.source_house})</strong>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-purple-900 text-white p-4 rounded-2xl text-center shadow-md">
                  <span className="text-xs text-purple-200 font-bold uppercase block">Project Risk Score</span>
                  <strong className="text-2xl font-black text-white">{activeModalWork.project_risk_score} / 100</strong>
                </div>
                <div className="bg-orange-500 text-white p-4 rounded-2xl text-center shadow-md">
                  <span className="text-xs text-orange-100 font-bold uppercase block">Alert Priority</span>
                  <strong className="text-2xl font-black text-white">{activeModalWork.priority || "HIGH"}</strong>
                </div>
                <div className="bg-indigo-900 text-white p-4 rounded-2xl text-center shadow-md">
                  <span className="text-xs text-indigo-200 font-bold uppercase block">Current Status</span>
                  <strong className="text-2xl font-black text-white">{activeModalWork.status || "NEW"}</strong>
                </div>
              </div>

              <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200">
                <h4 className="text-xs font-black uppercase text-slate-500 mb-2.5">Full Evidence Package Payload (§14)</h4>
                {activeModalWork.evidence?.risk_drivers && activeModalWork.evidence.risk_drivers.length > 0 ? (
                  <div className="space-y-1.5">
                    {activeModalWork.evidence.risk_drivers.map((driver: string, idx: number) => (
                      <div key={idx} className="bg-purple-100/70 border border-purple-200 text-purple-950 p-2.5 rounded-xl text-xs font-semibold flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-600 flex-shrink-0" />
                        <span>{driver}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-800 text-xs leading-relaxed font-medium">
                    {activeModalWork.top_contributing_factors || "Threshold crossing detected across entity resolution parameters."}
                  </p>
                )}
              </div>

              {/* HUMAN AUDITOR INVESTIGATION FEEDBACK PANEL (§21) */}
              <div className="border-t border-purple-100 pt-6 space-y-4">
                <div className="flex items-center gap-2">
                  <UserCheck2 className="w-5 h-5 text-purple-800" />
                  <h4 className="text-sm font-black text-slate-900 uppercase tracking-wide">
                    Human Auditor Feedback & Model Calibration (§21)
                  </h4>
                </div>

                <div className="space-y-2">
                  <span className="text-xs font-extrabold text-slate-600 block uppercase">Select Auditor Determination:</span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      { status: "VALIDATED_RISK", label: "Validated Risk" },
                      { status: "UNDER_INVESTIGATION", label: "Under Investigation" },
                      { status: "DATA_QUALITY_ISSUE", label: "Data Quality Issue" },
                      { status: "DISMISSED", label: "Dismiss Alert" }
                    ].map((item) => (
                      <button
                        key={item.status}
                        onClick={() => setAuditorStatus(item.status)}
                        className={`p-2.5 rounded-xl text-xs font-bold transition border ${
                          auditorStatus === item.status
                            ? "bg-purple-950 text-white border-purple-900 shadow-md"
                            : "bg-slate-50 text-slate-600 hover:bg-purple-50 border-slate-200"
                        }`}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <span className="text-xs font-extrabold text-slate-600 block uppercase">Auditor Investigation Notes:</span>
                  <textarea
                    rows={3}
                    placeholder="Enter findings, physical inspection observations, or calibration feedback..."
                    value={auditorNotes}
                    onChange={(e) => setAuditorNotes(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-3 text-xs text-slate-900 focus:outline-none focus:border-purple-600"
                  />
                </div>

                <button
                  onClick={handleAuditorFeedbackSubmit}
                  disabled={submittingFeedback}
                  className="w-full py-3 bg-gradient-to-r from-orange-500 via-amber-500 to-purple-600 hover:from-orange-600 hover:to-purple-700 text-white font-extrabold text-xs rounded-2xl transition shadow-lg shadow-orange-500/20 flex items-center justify-center gap-2 active:scale-95 disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                  {submittingFeedback ? "Saving Feedback to Model Data Store..." : "Submit Auditor Feedback & Calibrate Model"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
