import { ArrowRight, IndianRupee, Briefcase, FileText, CheckCircle2, ShieldCheck, Activity, Database } from "lucide-react";
import Link from "next/link";
import { getMpladsMetrics } from "@/lib/data";

export default function Home() {
  const summaryData = getMpladsMetrics();

  const formatCurrency = (val: number) => {
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    return `₹${val.toLocaleString()}`;
  };

  return (
    <div className="flex flex-col gap-12 font-body pb-20 pt-4">
      {/* Brand Header / Logo for landing page */}
      <div className="flex items-center justify-between">
        <div className="font-headline font-extrabold text-3xl text-primary tracking-tight">
          NIRIKSHAK<span className="text-secondary">AI</span>
        </div>
        <Link
          href="/projects"
          className="text-sm font-bold text-gray-600 hover:text-primary transition-colors"
        >
          View Projects &rarr;
        </Link>
      </div>

      {/* Hero Section */}
      <section className="bg-surface rounded-3xl p-8 md:p-16 shadow-medium border border-gray-100 relative overflow-hidden group">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-bold mb-6 border border-primary/20">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            MPLADS AI Monitoring & Analytical Platform
          </div>
          <h1 className="font-headline font-extrabold text-5xl md:text-6xl text-gray-900 leading-[1.1] tracking-tight mb-4">
            Monitoring India's Progress, <span className="text-primary">Real-time.</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-xl leading-relaxed">
            Track MPLADS fund utilization, discover local development works, evaluate delay risk, and ensure transparent progress across every constituency.
          </p>

          <div className="flex flex-wrap items-center gap-4">
            <Link
              href="/projects"
              className="bg-primary hover:bg-[var(--color-primary-hover)] active:bg-[var(--color-primary-active)] text-white font-bold py-3.5 px-8 rounded-full text-lg transition-all flex items-center gap-2 shadow-md hover:shadow-lg"
            >
              Explore All Projects <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute right-[-10%] top-[-20%] w-96 h-96 bg-tertiary/20 rounded-full blur-3xl group-hover:bg-tertiary/30 transition-all duration-700" />
        <div className="absolute right-[10%] bottom-[-20%] w-80 h-80 bg-secondary/20 rounded-full blur-3xl group-hover:bg-secondary/30 transition-all duration-700" />
      </section>

      {/* Highlights Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-subtle hover:shadow-medium transition-all">
          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4">
            <Database className="w-6 h-6" />
          </div>
          <h3 className="font-headline font-bold text-lg text-gray-900 mb-2">
            118 Engineered ML Features
          </h3>
          <p className="text-sm text-gray-500 leading-relaxed">
            Comprehensive pre-sanction, financial gap, lifecycle duration, and leakage-safe historical aggregates.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-subtle hover:shadow-medium transition-all">
          <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center text-secondary mb-4">
            <Activity className="w-6 h-6" />
          </div>
          <h3 className="font-headline font-bold text-lg text-gray-900 mb-2">
            AI Delay & Risk Prediction
          </h3>
          <p className="text-sm text-gray-500 leading-relaxed">
            Forecasting completion bottlenecks and fund stagnation using cross-dataset entity resolution.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-subtle hover:shadow-medium transition-all">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 mb-4">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="font-headline font-bold text-lg text-gray-900 mb-2">
            Constituency-Level Tracking
          </h3>
          <p className="text-sm text-gray-500 leading-relaxed">
            Both Lok Sabha and Rajya Sabha records mapped across 543+ constituencies and 37 states.
          </p>
        </div>
      </section>

      {/* Quick Summary Banner */}
      <section className="bg-gray-50 rounded-2xl p-8 border border-gray-200/60 flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <span className="text-xs font-bold text-primary uppercase tracking-wider">Live Nation-wide Tracking</span>
          <h3 className="font-headline font-bold text-2xl text-gray-900 mt-1">
            Over {summaryData.completed.toLocaleString()} works monitored across India
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Total Allocated: {formatCurrency(summaryData.allocated)} &bull; Total Expenditure: {formatCurrency(summaryData.expenditure)}
          </p>
        </div>
        <Link
          href="/projects"
          className="bg-gray-900 hover:bg-primary text-white font-bold py-3 px-6 rounded-xl text-sm transition-all flex items-center gap-2 shrink-0 shadow-sm"
        >
          Explore All Projects <ArrowRight className="w-4 h-4" />
        </Link>
      </section>
    </div>
  );
}
