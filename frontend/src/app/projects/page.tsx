"use client";

import React, { useState } from "react";
import FeatureWorkTable from "@/components/features/FeatureWorkTable";
import { Briefcase, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function ProjectsPage() {
  const [parliament, setParliament] = useState<string>("lok_sabha");

  return (
    <div className="flex flex-col gap-8 font-body pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary transition-colors mb-2 font-medium"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <Briefcase className="w-7 h-7 text-primary" />
            <h1 className="font-headline font-extrabold text-3xl md:text-4xl text-gray-900 tracking-tight">
              All MPLADS Development Projects
            </h1>
          </div>
          <p className="text-gray-600 mt-1 text-base">
            Explore complete work-level records, sanction amounts, expenditure utilization, and lifecycle milestones.
          </p>
        </div>

        {/* Parliament Switcher */}
        <div className="bg-surface p-1.5 rounded-xl border flex shadow-sm">
          <button
            onClick={() => setParliament("lok_sabha")}
            className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
              parliament === "lok_sabha"
                ? "bg-primary text-white shadow"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Lok Sabha
          </button>
          <button
            onClick={() => setParliament("rajya_sabha")}
            className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
              parliament === "rajya_sabha"
                ? "bg-primary text-white shadow"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Rajya Sabha
          </button>
        </div>
      </div>

      {/* Main Filterable Projects & Features Table */}
      <section>
        <FeatureWorkTable parliament={parliament} />
      </section>
    </div>
  );
}

