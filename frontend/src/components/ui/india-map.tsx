"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
import { motion, AnimatePresence } from "framer-motion";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  ConstituencyMPLADS,
  computeRiskScore,
  getRiskColor,
  getRiskLabel,
  getRiskBadgeClass,
  getMarkerRadius,
} from "@/lib/mplads";

// ─── Types ───────────────────────────────────────────────────────────────────

type FilterMode = "all" | "elevated" | "critical";

interface IndiaMapProps {
  constituencies?: ConstituencyMPLADS[];
  lastUpdated?: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const GEO_URL = "/data/india-states.json";

// Map new TopoJSON state names back to standard ones used in constituency data
const STATE_NAME_MAP: Record<string, string> = {
  "Andaman and Nicobar Islands": "Andaman and Nicobar",
  "Dadra and Nagar Haveli and Daman and Diu": "Dadra and Nagar Haveli",
};

function resolveStateScore(
  geoName: string,
  constituencies: ConstituencyMPLADS[]
): number | null {
  const normalized = STATE_NAME_MAP[geoName] ?? geoName;
  const relevant = constituencies.filter((c) => c.state === normalized);
  if (relevant.length === 0) return null;
  return Math.max(...relevant.map(computeRiskScore));
}

// Lighter shades for the map polygons so the dark dots pop out
function getStateRiskColor(score: number | null): string {
  if (score === null) return "#F8FAFC"; // Slate-50
  if (score >= 75) return "#FCA5A5";    // Red-300 (lighter than Red-600)
  if (score >= 50) return "#FED7AA";    // Orange-200 (lighter than Orange-400)
  if (score >= 25) return "#FEF08A";    // Yellow-200 (lighter than Yellow-300)
  return "#BBF7D0";                     // Green-200 (lighter than Green-500)
}

// ─── Component ───────────────────────────────────────────────────────────────

function toStateSlug(name: string): string {
  return name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

export function IndiaMap({
  constituencies = [],
  lastUpdated = "Aug 2026",
}: IndiaMapProps) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [filter, setFilter] = useState<FilterMode>("all");

  useEffect(() => { setMounted(true); }, []);

  const filteredConstituencies = constituencies.filter((c) => {
    const score = computeRiskScore(c);
    if (filter === "critical") return score >= 75;
    if (filter === "elevated") return score >= 50;
    return true;
  });

  if (!mounted) return null;

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", gap: "16px" }}>
      
      {/* ── Filter Toggle ─────────────────────────────────────────────────── */}
      <div style={{
        display: "flex", gap: "4px", padding: "4px",
        backgroundColor: "#F1F5F9", borderRadius: "9999px",
        border: "1px solid #E2E8F0",
      }}>
        {(["all", "elevated", "critical"] as FilterMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => setFilter(mode)}
            style={{
              padding: "6px 16px",
              borderRadius: "9999px",
              fontSize: "12px",
              fontWeight: 700,
              border: "none",
              cursor: "pointer",
              transition: "all 0.2s",
              backgroundColor: filter === mode ? "#FFFFFF" : "transparent",
              color: filter === mode ? "#0F172A" : "#64748B",
              boxShadow: filter === mode ? "0 1px 3px rgba(0,0,0,0.12)" : "none",
            }}
          >
            {mode === "all" ? "All Constituencies" : mode === "elevated" ? "Elevated+" : "Critical Only"}
          </button>
        ))}
      </div>

      {/* ── Map Container ─────────────────────────────────────────────────── */}
      {/*
        The ComposableMap renders an 800×600 SVG (landscape, 4:3).
        We match the container exactly to this ratio so there is no empty space.
        Using paddingTop trick for a reliable aspect-ratio in all browsers.
      */}
      <div
        className="india-map-wrapper"
        style={{
          position: "relative",
          width: "100%",
          margin: "0 auto",
          borderRadius: "16px",
          overflow: "hidden",
          border: "1px solid #E2E8F0",
          boxShadow: "0 4px 24px rgba(0,0,0,0.06)",
          backgroundColor: "#FFFFFF",
        }}
      >
        {/* Aspect ratio holder — 800×640 = 1.25:1 landscape */}
        <div style={{ paddingTop: "80%" }} />
        
        {/* Absolute fill for the SVG */}
        <div style={{ position: "absolute", inset: 0 }}>
          <TooltipProvider delay={80}>
            <ComposableMap
              width={800}
              height={640}
              projection="geoMercator"
              projectionConfig={{ scale: 1050, center: [83, 23] }}
              style={{ width: "100%", height: "100%" }}
            >
              {/* Explicit background rect — CSS style overrides any external fill rules */}
              <rect width="800" height="640" style={{ fill: "#FFFFFF" }} />

              {/* Tier 1: State choropleth */}
              <Geographies geography={GEO_URL}>
                {({ geographies }) =>
                  geographies.map((geo) => {
                    const geoName = geo.properties.st_nm || geo.properties.NAME_1 || geo.properties.name || "";
                    const score = resolveStateScore(geoName, constituencies);
                    const fill = getStateRiskColor(score);
                    const slug = toStateSlug(geoName);
                    return (
                      <Tooltip key={geo.rsmKey}>
                        <TooltipTrigger
                          render={
                            <Geography
                              geography={geo}
                              onClick={() => router.push(`/states/${slug}`)}
                              style={{
                                default: { fill, stroke: "#94A3B8", strokeWidth: 0.5, outline: "none", cursor: "pointer" },
                                hover:   { fill, stroke: "#475569", strokeWidth: 1,   outline: "none", filter: "brightness(0.88)", cursor: "pointer" },
                                pressed: { fill, stroke: "#475569", strokeWidth: 1,   outline: "none", cursor: "pointer" },
                              }}
                            />
                          }
                        />
                        <TooltipContent
                          style={{
                            padding: "8px 12px",
                            backgroundColor: "white",
                            border: "1px solid #E2E8F0",
                            borderRadius: "8px",
                            boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                            zIndex: 50,
                          }}
                        >
                          <div style={{ fontWeight: 600, color: "#0F172A", fontSize: "13px" }}>{geoName}</div>
                          <div style={{ color: "#64748B", fontSize: "11px" }}>
                            {score !== null
                              ? `Max Risk: ${score}/100 — ${getRiskLabel(score)}`
                              : "No constituency data"}
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })
                }
              </Geographies>

              {/* Tier 2: Constituency markers */}
              <AnimatePresence>
                {filteredConstituencies.map((c, index) => {
                  const score = computeRiskScore(c);
                  const color = getRiskColor(score);
                  const radius = getMarkerRadius(score, score >= 75);

                  return (
                    <Marker key={c.id} coordinates={[c.lng, c.lat]}>
                      <Tooltip>
                        <TooltipTrigger
                          render={
                            <g
                              className="outline-none cursor-pointer"
                              onClick={() => {
                                const stateSlug = toStateSlug(c.state);
                                router.push(`/states/${stateSlug}`);
                              }}
                            >
                              {/* Invisible larger hover target */}
                              <circle r={Math.max(radius + 10, 14)} fill="transparent" />
                              
                              {/* Core dot */}
                              <motion.circle
                                r={radius}
                                fill={color}
                                stroke="white"
                                strokeWidth={1.2}
                                initial={{ scale: 0, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                transition={{ delay: index * 0.015, type: "spring", stiffness: 280, damping: 22 }}
                              />
                            </g>
                          }
                        />
                        <TooltipContent style={{ maxWidth: "290px", padding: "12px", backgroundColor: "white", border: "1px solid #E2E8F0", borderRadius: "10px", boxShadow: "0 8px 24px rgba(0,0,0,0.12)" }}>
                          <ConstituencyTooltipCard c={c} score={score} />
                        </TooltipContent>
                      </Tooltip>
                    </Marker>
                  );
                })}
              </AnimatePresence>
            </ComposableMap>
          </TooltipProvider>
        </div>
      </div>

      {/* ── Legend ────────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 20px", justifyContent: "center", fontSize: "12px", color: "#475569" }}>
        {[
          { color: "#F1F5F9", label: "No Data",       border: true },
          { color: "#22C55E", label: "Healthy (0–24)" },
          { color: "#FDE047", label: "Watch (25–49)",  border: true },
          { color: "#FB923C", label: "Elevated (50–74)" },
          { color: "#DC2626", label: "Critical (75–100)" },
        ].map(({ color, label, border }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{
              width: "11px", height: "11px", borderRadius: "50%",
              backgroundColor: color, display: "inline-block", flexShrink: 0,
              border: border ? "1px solid #CBD5E1" : undefined,
            }} />
            {label}
          </div>
        ))}
      </div>

      {/* ── Data Source ───────────────────────────────────────────────────── */}
      <p style={{ fontSize: "11px", color: "#94A3B8", textAlign: "center", marginTop: "4px" }}>
        Source: MPLADS public dataset (mplads.gov.in) · Last updated: {lastUpdated} · Risk scoring: NIRIKSHAK AI model v0.1
      </p>
    </div>
  );
}

// ─── Constituency Tooltip Card ────────────────────────────────────────────────

function ConstituencyTooltipCard({ c, score }: { c: ConstituencyMPLADS; score: number }) {
  const utilPct = Math.round((c.utilizedAmount / (c.releasedAmount || 1)) * 100);
  const topFlag = [...c.anomalyFlags].sort((a, b) => {
    const w: Record<string, number> = { critical: 3, high: 2, medium: 1, low: 0 };
    return (w[b.severity] ?? 0) - (w[a.severity] ?? 0);
  })[0];

  const flagTypeLabel: Record<string, string> = {
    fund_diversion:        "Fund Diversion",
    inflated_billing:      "Inflated Billing",
    ghost_works:           "Ghost Works",
    delayed_utilization:   "Delayed Utilization",
    vendor_repeat_pattern: "Vendor Repeat Pattern",
    other:                 "Other",
  };

  const badgeStyle = getRiskBadgeClass(score);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontFamily: "inherit" }}>
      {/* Header */}
      <div>
        <div style={{ fontWeight: 700, color: "#0F172A", fontSize: "13px", lineHeight: "1.3" }}>
          {c.name} <span style={{ fontWeight: 400, color: "#64748B" }}>— {c.state}</span>
        </div>
        <div style={{ fontSize: "11px", color: "#64748B", marginTop: "2px" }}>
          MP: {c.mpName}{c.party ? ` (${c.party})` : ""}
        </div>
      </div>

      {/* Risk score row */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span style={{ fontSize: "12px", fontWeight: 600, color: "#0F172A" }}>
          Risk: {score}/100
        </span>
        <span className={badgeStyle} style={{
          fontSize: "10px", fontWeight: 700, padding: "2px 8px",
          borderRadius: "9999px", textTransform: "uppercase", letterSpacing: "0.05em",
        }}>
          {getRiskLabel(score)}
        </span>
      </div>

      {/* Fund grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "4px", fontSize: "11px" }}>
        {[
          { val: `₹${c.sanctionedAmount}Cr`, label: "Sanctioned", bg: "#F8FAFC" },
          { val: `₹${c.releasedAmount}Cr`,   label: "Released",   bg: "#F8FAFC" },
          { val: `₹${c.utilizedAmount}Cr (${utilPct}%)`, label: "Utilized",
            bg: utilPct < 50 ? "#FEF2F2" : utilPct < 80 ? "#FFF7ED" : "#F0FDF4" },
        ].map(({ val, label, bg }) => (
          <div key={label} style={{ backgroundColor: bg, borderRadius: "6px", padding: "5px 4px", textAlign: "center" }}>
            <div style={{ fontWeight: 700, color: "#0F172A", fontSize: "11px" }}>{val}</div>
            <div style={{ color: "#64748B", fontSize: "10px" }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Works row */}
      <div style={{ fontSize: "11px", color: "#334155" }}>
        Works: <strong>{c.worksRecommended}</strong> rec ·{" "}
        <span style={{ color: "#16A34A", fontWeight: 600 }}>{c.worksCompleted} done</span> ·{" "}
        <span style={{ color: "#DC2626", fontWeight: 600 }}>{c.worksPending} pending</span>
      </div>

      {/* Staleness */}
      <div style={{ fontSize: "11px", color: "#334155" }}>
        Unspent balance age:{" "}
        <strong style={{ color: c.unspentBalanceAgeMonths > 18 ? "#DC2626" : "#0F172A" }}>
          {c.unspentBalanceAgeMonths} months
        </strong>
      </div>

      {/* Top flag */}
      {topFlag && (
        <div style={{ fontSize: "11px", borderTop: "1px solid #F1F5F9", paddingTop: "6px" }}>
          <span style={{ color: "#64748B" }}>Top flag: </span>
          <strong style={{ color: "#0F172A" }}>{flagTypeLabel[topFlag.type] ?? topFlag.type}</strong>
          <span className={getRiskBadgeClass(
            topFlag.severity === "critical" ? 80 : topFlag.severity === "high" ? 60 : topFlag.severity === "medium" ? 35 : 10
          )} style={{ marginLeft: "6px", fontSize: "10px", fontWeight: 700, padding: "1px 6px", borderRadius: "9999px", textTransform: "uppercase" }}>
            {topFlag.severity}
          </span>
        </div>
      )}
    </div>
  );
}
