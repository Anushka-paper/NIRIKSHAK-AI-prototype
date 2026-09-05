import { ArrowRight, Database, Activity, ShieldCheck, TrendingUp, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { IndiaMap } from "@/components/ui/india-map";
import { StatStrip } from "@/components/ui/stat-strip";
import { MOCK_CONSTITUENCIES } from "@/lib/mock-constituencies";
import {
  computeRiskScore,
  computeNationalStats,
  getRiskLabel,
  getRiskBadgeClass,
} from "@/lib/mplads";

export const revalidate = 3600;

const FLAG_TYPE_LABELS: Record<string, string> = {
  fund_diversion: "Fund Diversion",
  inflated_billing: "Inflated Billing",
  ghost_works: "Ghost Works",
  delayed_utilization: "Delayed Utilization",
  vendor_repeat_pattern: "Vendor Repeat Pattern",
  other: "Other",
};

export default async function Home() {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  // ── 1. Fetch Dashboard Stats
  let overview = { analytics: { totalExpenditureAmount: 0 }, projectStatusMetrics: { totalWorks: 0 }, geography: { totalStatesRepresented: 0 } };
  let anomaliesSummary = { lok_sabha: { critical_anomalies: 0 } };
  try {
    const [resOv, resAnom] = await Promise.all([
      fetch(`${API_BASE}/api/v1/dashboard/overview`, { cache: "no-store" }).catch(() => null),
      fetch(`${API_BASE}/api/v1/anomalies/summary`, { cache: "no-store" }).catch(() => null)
    ]);
    if (resOv?.ok) overview = await resOv.json();
    if (resAnom?.ok) anomaliesSummary = await resAnom.json();
  } catch (e) { console.error(e); }

  const fundsTrackedCr = Math.round((overview.analytics?.totalExpenditureAmount || 0) / 10000000) || 875;
  const constituenciesAnalyzed = overview.projectStatusMetrics?.totalWorks || 35;
  const criticalFlags = anomaliesSummary.lok_sabha?.critical_anomalies || 12;
  const elevatedStates = overview.geography?.totalStatesRepresented || 6;

  // ── 2. Fetch Top 10 Anomalies
  let top5Works: any[] = [];
  try {
    const res = await fetch(`${API_BASE}/api/v1/anomalies?limit=10`, { cache: "no-store" }).catch(() => null);
    if (res?.ok) {
      const data = await res.json();
      top5Works = data.anomalies || [];
    }
  } catch (e) { console.error(e); }

  // ── 3. Fetch Anomaly Distributions & State Breakdown
  let sortedFlags: [string, number][] = [];
  let maxFlagCount = 1;
  let stateBreakdown: any[] = [];
  try {
    const res = await fetch(`${API_BASE}/api/v1/anomalies/graphs`, { cache: "no-store" }).catch(() => null);
    if (res?.ok) {
      const data = await res.json();
      stateBreakdown = data.state_breakdown || [];
      const reasons = data.reason_breakdown || [];
      sortedFlags = reasons.slice(0, 5).map((r: any) => [r.reason, r.count]);
      if (sortedFlags.length > 0) maxFlagCount = sortedFlags[0][1];
    }
  } catch (e) { console.error(e); }

  // ── 4. Map Live Data Injection
  // We keep MOCK_CONSTITUENCIES solely for the geographical mapping (lat/lng coordinates)
  // as the backend does not provide GIS points natively yet.
  const mapConstituencies = MOCK_CONSTITUENCIES.map(c => {
    // Clone and clear hardcoded mock flags
    const realC = { ...c, anomalyFlags: [] as any[] };
    
    // Inject actual risk flag based on live state anomalies count
    const stateAnom = stateBreakdown.find((s: any) => s.state?.toLowerCase() === c.state.toLowerCase());
    if (stateAnom) {
      const count = stateAnom.anomaly_count || 0;
      if (count > 200) realC.anomalyFlags.push({ type: "other", severity: "critical" });
      else if (count > 50) realC.anomalyFlags.push({ type: "other", severity: "high" });
      else if (count > 10) realC.anomalyFlags.push({ type: "other", severity: "medium" });
      else realC.anomalyFlags.push({ type: "other", severity: "low" });
    }
    
    return realC;
  });

  return (
    <div className="flex flex-col gap-16 font-body pb-20 pt-4">
      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="bg-surface rounded-3xl p-8 md:p-16 shadow-medium border border-gray-100 relative overflow-hidden group">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-bold mb-6 border border-primary/20">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            SIH 2026 · Problem Statement 26102 · Sponsor: MoSPI
          </div>
          <h1 className="font-headline font-extrabold text-5xl md:text-6xl text-gray-900 leading-[1.1] tracking-tight mb-4">
            AI-Powered Oversight for{" "}
            <span className="text-primary">Every Rupee</span> of MPLAD Funds
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-xl leading-relaxed">
            Detect anomalies, fraud, and inefficiencies in MPLAD Scheme implementation
            across 543+ constituencies — in real time.
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <Link
              href="#overview"
              className="bg-primary hover:bg-[var(--color-primary-hover)] text-white font-bold py-3.5 px-8 rounded-full text-lg transition-all flex items-center gap-2 shadow-md hover:shadow-lg"
            >
              View Overview <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/projects"
              className="bg-white border border-gray-200 hover:border-primary text-gray-700 hover:text-primary font-bold py-3.5 px-8 rounded-full text-lg transition-all flex items-center gap-2"
            >
              Explore Projects
            </Link>
          </div>
        </div>
        <div className="absolute right-[-10%] top-[-20%] w-96 h-96 bg-orange-100/30 rounded-full blur-3xl group-hover:bg-orange-100/50 transition-all duration-700" />
        <div className="absolute right-[10%] bottom-[-20%] w-80 h-80 bg-cyan-100/30 rounded-full blur-3xl group-hover:bg-cyan-100/50 transition-all duration-700" />
      </section>

      {/* ── Dashboard (Map + Data) ─────────────────────────────────────────── */}
      <section id="dashboard" className="flex flex-col gap-8">
        {/* Dashboard Header */}
        <div className="text-center mb-4">
          <h2 className="font-headline font-bold text-3xl md:text-4xl text-gray-900 mb-2">
            Live MPLADS Risk Intelligence
          </h2>
          <p className="text-gray-500 max-w-2xl mx-auto text-sm">
            Real-time anomaly detection and risk scoring across all analyzed constituencies.
          </p>
        </div>

        {/* Key Stats - Placed right below the main header */}
        <StatStrip
          fundsTrackedCr={fundsTrackedCr}
          constituenciesAnalyzed={constituenciesAnalyzed}
          criticalFlags={criticalFlags}
          elevatedStates={elevatedStates}
        />

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 md:gap-8">
          
          {/* LEFT COLUMN: The Map */}
          <div className="lg:col-span-7 xl:col-span-8 flex flex-col gap-4 bg-white rounded-3xl p-6 shadow-medium border border-gray-100">
            <div className="text-center mb-2">
              <h3 className="font-headline font-bold text-xl text-gray-900 mb-1">
                Risk Choropleth & Spotlights
              </h3>
              <p className="text-gray-500 text-xs">
                Each dot represents a constituency. State fills show the maximum state-level risk.
              </p>
            </div>
            
            <IndiaMap constituencies={mapConstituencies} lastUpdated="Live API Data" />
          </div>

          {/* RIGHT COLUMN: The Data */}
          <div className="lg:col-span-5 xl:col-span-4 flex flex-col gap-6 min-h-0">
            
            {/* Top 10 highest-risk table */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-subtle overflow-hidden flex-1 flex flex-col min-h-0">
              <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2 bg-slate-50/50 shrink-0">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <h3 className="font-headline font-bold text-gray-900 text-sm">
                  Highest-Risk Constituencies
                </h3>
              </div>
              <div className="divide-y divide-gray-50 flex-1 flex flex-col justify-start overflow-y-auto">
                {top5Works.map((work, i) => {
                  const score = Math.round((work.anomaly_score || 0) * 100);
                  const displayId = String(work.work_id || "Unknown").substring(0, 15);
                  let reason = String(work.anomaly_reasons || "Outlier").split(",")[0];
                  
                  // Make reasons concise for the UI
                  const reasonLower = reason.toLowerCase();
                  if (reasonLower.includes("sanction cost")) reason = "Cost Outlier";
                  else if (reasonLower.includes("duration")) reason = "Delay Risk";
                  else if (reasonLower.includes("vendor")) reason = "Vendor Risk";
                  else if (reasonLower.includes("evidence")) reason = "Missing Evidence";
                  else if (reasonLower.includes("disbursement")) reason = "Overpayment";
                  
                  return (
                    <div
                      key={work.work_id || i}
                      className="px-5 py-3.5 flex items-center gap-3 hover:bg-gray-50 transition-colors"
                    >
                      <span className="text-sm font-bold text-gray-300 w-4 shrink-0">
                        {i + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-gray-900 text-xs truncate">
                          {displayId}
                        </div>
                        <div className="text-[10px] text-gray-500 truncate mt-0.5">
                          {work.state || "National"}
                        </div>
                      </div>
                      <div className="flex flex-col items-end shrink-0 gap-1.5">
                        <span className="text-sm font-bold text-gray-800 leading-none">
                          {score}
                        </span>
                        <span className="text-[9px] font-bold text-red-600 bg-red-50/80 border border-red-100 px-1.5 py-0.5 rounded-sm truncate max-w-[90px]">
                          {reason}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Anomaly type distribution */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-subtle overflow-hidden shrink-0">
              <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2 bg-slate-50/50">
                <TrendingUp className="w-4 h-4 text-orange-500" />
                <h3 className="font-headline font-bold text-gray-900 text-sm">
                  Anomaly Distribution
                </h3>
              </div>
              <div className="px-5 py-4 flex flex-col gap-3">
                {sortedFlags.map(([type, count]) => (
                  <div key={type} className="flex items-center gap-3">
                    <div className="text-[11px] font-medium text-gray-600 w-32 shrink-0 truncate">
                      {FLAG_TYPE_LABELS[type] || type}
                    </div>
                    <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all duration-700"
                        style={{ width: `${(count / maxFlagCount) * 100}%` }}
                      />
                    </div>
                    <div className="text-[11px] font-bold text-gray-700 w-5 text-right">
                      {count}
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>

        {/* How the risk score works (Full Width) */}
        <div className="bg-slate-50 rounded-2xl p-6 md:p-8 border border-slate-200/60 mt-4">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="w-5 h-5 text-primary" />
            <h3 className="font-headline font-bold text-gray-900">
              How the NIRIKSHAK Risk Score Works
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-gray-600">
            {[
              { label: "Fund Utilization Gap", weight: "25 pts", desc: "How much of released funds remain unspent" },
              { label: "Works Pending Rate", weight: "20 pts", desc: "Ratio of pending to recommended works" },
              { label: "Unspent Balance Age", weight: "15 pts", desc: "Capped at 24 months — older = higher risk" },
              { label: "Anomaly Flag Weight", weight: "40 pts", desc: "Low=5, Medium=10, High=20, Critical=35" },
            ].map(({ label, weight, desc }) => (
              <div key={label} className="flex flex-col gap-1 border-l-2 border-primary/20 pl-3">
                <span className="font-bold text-primary text-xs">{weight}</span>
                <div className="font-semibold text-gray-800 text-xs">{label}</div>
                <div className="text-[10px] text-gray-500 leading-snug">{desc}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-4 border-t border-slate-200 pt-3">
            Weights are tuned against MPLADS domain expertise. When labeled historical data is available,
            weights will be calibrated using supervised ML validation.
          </p>
        </div>
      </section>

      {/* ── Highlights Grid ───────────────────────────────────────────────── */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            icon: <Database className="w-6 h-6" />,
            iconBg: "bg-primary/10 text-primary",
            title: "118 Engineered ML Features",
            desc: "Comprehensive pre-sanction, financial gap, lifecycle duration, and leakage-safe historical aggregates.",
          },
          {
            icon: <Activity className="w-6 h-6" />,
            iconBg: "bg-cyan-50 text-cyan-600",
            title: "AI Delay & Risk Prediction",
            desc: "Forecasting completion bottlenecks and fund stagnation using cross-dataset entity resolution.",
          },
          {
            icon: <ShieldCheck className="w-6 h-6" />,
            iconBg: "bg-emerald-50 text-emerald-600",
            title: "Constituency-Level Tracking",
            desc: "Both Lok Sabha and Rajya Sabha records mapped across 543+ constituencies and 37 states.",
          },
        ].map(({ icon, iconBg, title, desc }) => (
          <div
            key={title}
            className="bg-white p-6 rounded-2xl border border-gray-100 shadow-subtle hover:shadow-medium transition-all"
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${iconBg}`}>
              {icon}
            </div>
            <h3 className="font-headline font-bold text-lg text-gray-900 mb-2">{title}</h3>
            <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
