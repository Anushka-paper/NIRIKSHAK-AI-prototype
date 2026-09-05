"use client";

import React, { useEffect, useState, useRef } from "react";
import { useInView } from "framer-motion";

interface StatProps {
  value: number;
  label: string;
  prefix?: string;
  suffix?: string;
}

function AnimatedStat({ value, label, prefix = "", suffix = "" }: StatProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    let startTs: number | null = null;
    const duration = 2000;
    const step = (ts: number) => {
      if (!startTs) startTs = ts;
      const progress = Math.min((ts - startTs) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 5);
      setCurrent(Math.floor(ease * value));
      if (progress < 1) window.requestAnimationFrame(step);
      else setCurrent(value);
    };
    window.requestAnimationFrame(step);
  }, [isInView, value]);

  return (
    <div ref={ref} className="flex flex-col items-center justify-center gap-1 px-4 py-2">
      <div className="text-3xl md:text-4xl font-bold tracking-tighter text-slate-900 font-headline">
        {prefix}
        {current.toLocaleString()}
        {suffix}
      </div>
      <div className="text-xs font-semibold text-slate-500 text-center uppercase tracking-widest">
        {label}
      </div>
    </div>
  );
}

interface StatStripProps {
  fundsTrackedCr?: number;
  constituenciesAnalyzed?: number;
  criticalFlags?: number;
  elevatedStates?: number;
}

export function StatStrip({
  fundsTrackedCr = 2715,
  constituenciesAnalyzed = 37,
  criticalFlags = 124,
  elevatedStates = 11,
}: StatStripProps) {
  return (
    <div className="w-full max-w-5xl mx-auto py-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-0 divide-y-2 md:divide-y-0 md:divide-x divide-slate-200">
        <AnimatedStat
          value={fundsTrackedCr}
          label="Crore Tracked"
          prefix="₹"
          suffix=" Cr"
        />
        <AnimatedStat
          value={constituenciesAnalyzed}
          label="Constituencies Analyzed"
        />
        <AnimatedStat
          value={criticalFlags}
          label="Critical Flags"
        />
        <AnimatedStat
          value={elevatedStates}
          label="States with Elevated Risk"
        />
      </div>
    </div>
  );
}
