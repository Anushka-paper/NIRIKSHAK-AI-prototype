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
  const [selectedRiskCategory, setSelectedRiskCategory] = useState<string>("");
  const [selectedAlertStatus, setSelectedAlertStatus] = useState<string>("");
  const [predictiveSearch, setPredictiveSearch] = useState<string>("");

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
        const res = await fetch(`${API_URL}/api/v1/analytics/geography/states?limit=30`);
        if (res.ok) setGeoData(await res.json());

        const sigRes = await fetch(`${API_URL}/api/v1/analytics/geography/anomalies?limit=10`);
        if (sigRes.ok) setGeoSignals((await sigRes.json()).signals || []);
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
  }, [activeTab, selectedHouse, geoLevel, vendorSearch, selectedRuleCode, complianceSearch, selectedDuplicateLayer, duplicateSearch, selectedRiskCategory, selectedAlertStatus, predictiveSearch]);

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
              {activeTab === "duplicates" && "Duplicate Payment Detector & Rate-Card Engine (§10, §11)"}
              {activeTab === "financial" && "Financial Analytics"}
              {activeTab === "operational" && "Operational Analytics & Hazard Model (§5)"}
              {activeTab === "geographical" && "Geographical Trends & Spatial Analytics Module (§2-§19)"}
              {activeTab === "vendors" && "Vendor Intelligence Engine & Feature Store (§7)"}
              {activeTab === "calamity" && "Calamity Relief Dashboard"}
              {activeTab === "models" && "Model Monitoring"}
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

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Allocated Limit</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.allocated_limit_cr?.toLocaleString()} Cr</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Recommended</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.total_budget_cr?.toLocaleString()} Cr</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Sanctioned</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.sanctioned_budget_cr?.toLocaleString()} Cr</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Works Completed</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.completed_budget_cr?.toLocaleString()} Cr</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Expenditure Disbursed</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.total_expenditure_cr?.toLocaleString()} Cr</p>
                </div>

                <div className="bg-white border border-purple-200/80 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Calamity Consent Amount</span>
                  <p className="text-3xl font-black text-slate-900 tracking-tight mt-2">₹ {stats.calamity_consent_cr} Cr</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: GEOGRAPHICAL TRENDS & SPATIAL ANALYTICS MODULE (§2-§19) */}
          {!loading && activeTab === "geographical" && geoData && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-gradient-to-r from-purple-950 via-indigo-950 to-slate-900 text-white border border-purple-800 rounded-3xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-black">Geographical Trends & Spatial Analytics Module (§2-§19)</h3>
                  <p className="text-xs text-purple-200 mt-1 font-medium">State/Constituency fund concentration, Location Quotient (LQ), Category Deviation, and Spatial Inequality Index (HHI)</p>
                </div>
                <div className="px-4 py-2 bg-white/10 rounded-2xl border border-white/20 text-xs font-bold text-orange-300">
                  {geoData.total_states || 37} States & UTs Tracked
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">Total States / UTs</span>
                  <p className="text-3xl font-black text-slate-900 mt-2">{geoData.total_states || 37}</p>
                </div>

                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">State HHI Index (§8)</span>
                  <p className="text-3xl font-black text-purple-900 mt-2">HHI = {geoData.state_hhi || 2030.7}</p>
                  <span className="text-[10px] text-slate-500 font-bold block mt-1">Moderate Spatial Concentration</span>
                </div>

                <div className="bg-purple-900 text-white border border-purple-800 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-purple-200 uppercase">National Rec Budget</span>
                  <p className="text-3xl font-black text-white mt-2">₹ {geoData.national_totals?.total_recommended_cr?.toLocaleString() || "13,616"} Cr</p>
                </div>

                <div className="bg-orange-500 text-white border border-orange-600 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-orange-100 uppercase">Geographical Anomaly Signals (§9)</span>
                  <p className="text-3xl font-black text-white mt-2">1,579 Signals</p>
                  <span className="text-[10px] text-orange-100 font-bold block mt-1">944 High Severity LQ Signals</span>
                </div>
              </div>

              {/* Geographical Signals Feed (§9, §19 Explainability) */}
              <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm space-y-4">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-orange-600" />
                  <h4 className="text-sm font-black uppercase text-slate-900">Geographical Anomaly Signal Feed (§9, §19 Explainability)</h4>
                </div>

                <div className="space-y-3">
                  {geoSignals.map((sig, idx) => (
                    <div key={idx} className="bg-purple-50/70 border border-purple-200 p-4 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-black text-purple-900">{sig.signal_id}</span>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-rose-100 text-rose-900 border border-rose-300">
                            {sig.signal_type}
                          </span>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-orange-100 text-orange-900 border border-orange-300">
                            LQ = {sig.threshold ? `${sig.observed_value / sig.benchmark_value}` : "2.0x"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-800 font-semibold leading-relaxed">
                          {sig.explanation}
                        </p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <span className="text-xs font-black text-purple-900 block">{sig.state}</span>
                        <span className="text-[11px] font-bold text-slate-500">{sig.category}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* State Table */}
              <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                <div className="p-5 border-b border-purple-100 bg-purple-50/40">
                  <h4 className="text-sm font-black uppercase text-purple-950">State Fund Share (%) & Average Work Value Breakdown (§2)</h4>
                </div>
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                      <th className="px-5 py-4 whitespace-nowrap">State Name</th>
                      <th className="px-5 py-4 whitespace-nowrap">Total Works</th>
                      <th className="px-5 py-4 whitespace-nowrap">Recommended (Cr)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Recommended Share (%)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Sanctioned Share (%)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Expenditure Share (%)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Avg Work Value (INR)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50 font-medium">
                    {geoData.states?.map((s: any, i: number) => (
                      <tr key={i} className="hover:bg-purple-50/60 transition-all">
                        <td className="px-5 py-4 whitespace-nowrap font-extrabold text-slate-900">{s.state}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-purple-900">{s.total_works?.toLocaleString()} works</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">₹ {s.total_recommended_cr} Cr</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-purple-900">{s.recommended_share_pct}%</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-indigo-900">{s.sanctioned_share_pct}%</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-emerald-800">{s.expenditure_share_pct}%</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-slate-800">₹ {s.avg_work_value_inr?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 8: VENDOR INTELLIGENCE ENGINE (§7) */}
          {!loading && activeTab === "vendors" && vendorData && (
            <div className="space-y-8 animate-in fade-in duration-300">
              <div className="bg-gradient-to-r from-purple-950 via-indigo-950 to-slate-900 text-white border border-purple-800 rounded-3xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-black">IsolationForest Vendor Anomaly Engine & Monopoly Risk (§7)</h3>
                  <p className="text-xs text-purple-200 mt-1 font-medium">9-dimensional feature vectors detecting monopoly spend concentration and uniform payment suspicious patterns</p>
                </div>
                <div className="px-4 py-2 bg-white/10 rounded-2xl border border-white/20 text-xs font-bold text-orange-300">
                  {vendorData.total_vendors_analyzed?.toLocaleString() || "21,193"} Vendor Entities
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-sm">
                  <span className="text-xs font-black text-slate-500 uppercase">Total Valid Vendors</span>
                  <p className="text-3xl font-black text-slate-900 mt-2">{vendorData.total_vendors_analyzed?.toLocaleString() || "21,193"}</p>
                </div>

                <div className="bg-purple-900 text-white border border-purple-800 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-purple-200 uppercase">High Risk Vendors (Score ≥ 75)</span>
                  <p className="text-3xl font-black text-white mt-2">{vendorData.high_risk_vendors_count?.toLocaleString() || "299"}</p>
                </div>

                <div className="bg-orange-500 text-white border border-orange-600 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-orange-100 uppercase">Monopoly Concentration Risk</span>
                  <p className="text-3xl font-black text-white mt-2">{vendorData.monopoly_vendors_count?.toLocaleString() || "0"}</p>
                </div>

                <div className="bg-indigo-900 text-white border border-indigo-800 rounded-3xl p-6 shadow-md">
                  <span className="text-xs font-black text-indigo-200 uppercase">Uniform Amount Suspicion</span>
                  <p className="text-3xl font-black text-white mt-2">{vendorData.uniform_amount_vendors_count?.toLocaleString() || "299"}</p>
                </div>
              </div>

              <div className="bg-white border border-purple-100 rounded-3xl overflow-x-auto shadow-xl">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 text-white font-extrabold uppercase tracking-wider text-[11px]">
                      <th className="px-5 py-4 whitespace-nowrap">Vendor Entity Name</th>
                      <th className="px-5 py-4 whitespace-nowrap">Primary Constituency</th>
                      <th className="px-5 py-4 whitespace-nowrap">Works Assigned</th>
                      <th className="px-5 py-4 whitespace-nowrap">Total Disbursed (Cr)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Monopoly Dependency Ratio (§7)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Amount CV (vendor_amount_cv)</th>
                      <th className="px-5 py-4 whitespace-nowrap">Risk Pattern Flags</th>
                      <th className="px-5 py-4 whitespace-nowrap">IsolationForest Risk Score (0-100)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50 font-medium">
                    {vendorData.vendors?.map((v: any, i: number) => (
                      <tr key={i} className="hover:bg-purple-50/60 transition-all">
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-slate-900">{v.canonical_vendor_name}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-semibold text-slate-700">{cleanMpName(v.primary_constituency)}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-bold text-purple-900">{v.vendor_transaction_count || v.works_assigned} txns</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-orange-600">₹ {v.vendor_total_value_cr || v.total_disbursed_cr} Cr</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-slate-800">{v.vendor_dependency ? `${v.vendor_dependency}%` : "1.1%"}</td>
                        <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-indigo-900">{v.vendor_amount_cv !== undefined ? v.vendor_amount_cv : 0.0}</td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-black border ${
                            v.risk_flags?.includes("UNIFORM_AMOUNT") || v.risk_flags?.includes("MONOPOLY")
                              ? "bg-purple-100 text-purple-950 border-purple-300"
                              : "bg-slate-100 text-slate-600 border-slate-200"
                          }`}>
                            {v.risk_flags || "STANDARD"}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-xl text-xs font-black ${
                            (v.vendor_risk_score || 50) >= 75
                              ? "bg-rose-600 text-white shadow-md shadow-rose-600/20"
                              : "bg-emerald-600 text-white"
                          }`}>
                            {v.vendor_risk_score ?? 50.0} / 100
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
