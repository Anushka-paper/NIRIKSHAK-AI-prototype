// NIRIKSHAK AI — MPLADS Data Types & Risk Scoring
// SIH Problem Statement 26102

export type AnomalyFlagType =
  | "fund_diversion"
  | "inflated_billing"
  | "ghost_works"
  | "delayed_utilization"
  | "vendor_repeat_pattern"
  | "other";

export type AnomalySeverity = "low" | "medium" | "high" | "critical";

export interface AnomalyFlag {
  type: AnomalyFlagType;
  severity: AnomalySeverity;
  description?: string;
}

export interface ConstituencyMPLADS {
  id: string;
  name: string;
  state: string;
  mpName: string;
  party?: string;
  lat: number;
  lng: number;
  sanctionedAmount: number;
  releasedAmount: number;
  utilizedAmount: number;
  worksRecommended: number;
  worksCompleted: number;
  worksPending: number;
  unspentBalanceAgeMonths: number;
  anomalyFlags: AnomalyFlag[];
  lastUpdated?: string;
}

const SEVERITY_WEIGHTS: Record<AnomalySeverity, number> = {
  low: 5,
  medium: 10,
  high: 20,
  critical: 35,
};

export function computeRiskScore(c: ConstituencyMPLADS): number {
  const utilizationRate = c.utilizedAmount / (c.releasedAmount || 1);
  const utilizationGap = Math.max(0, 1 - utilizationRate);
  const pendingRate = c.worksPending / (c.worksRecommended || 1);
  const staleness = Math.min(c.unspentBalanceAgeMonths / 24, 1);
  const flagWeight = c.anomalyFlags.reduce(
    (sum, f) => sum + (SEVERITY_WEIGHTS[f.severity] ?? 5),
    0
  );
  const score =
    utilizationGap * 25 +
    pendingRate * 20 +
    staleness * 15 +
    Math.min(flagWeight, 40);
  return Math.round(Math.min(score, 100));
}

export type RiskTier = "none" | "healthy" | "watch" | "elevated" | "critical";

export function getRiskTier(score: number | null): RiskTier {
  if (score === null) return "none";
  if (score < 25) return "healthy";
  if (score < 50) return "watch";
  if (score < 75) return "elevated";
  return "critical";
}

export function getRiskColor(score: number | null): string {
  const tier = getRiskTier(score);
  const colors: Record<RiskTier, string> = {
    none:     "#F1F5F9",
    healthy:  "#22C55E",
    watch:    "#FDE047",
    elevated: "#FB923C",
    critical: "#DC2626",
  };
  return colors[tier];
}

export function getRiskLabel(score: number | null): string {
  const tier = getRiskTier(score);
  const labels: Record<RiskTier, string> = {
    none:     "No Data",
    healthy:  "Healthy",
    watch:    "Watch",
    elevated: "Elevated Risk",
    critical: "Critical",
  };
  return labels[tier];
}

export function getRiskBadgeClass(score: number | null): string {
  const tier = getRiskTier(score);
  const classes: Record<RiskTier, string> = {
    none:     "bg-slate-100 text-slate-500",
    healthy:  "bg-green-100 text-green-800",
    watch:    "bg-yellow-100 text-yellow-800",
    elevated: "bg-orange-100 text-orange-800",
    critical: "bg-red-100 text-red-800",
  };
  return classes[tier];
}

export function getPulseDuration(score: number): number {
  if (score >= 75) return 0.9;
  if (score >= 50) return 1.8;
  if (score >= 25) return 3.0;
  return 0;
}

export function getMarkerRadius(score: number, isMajor: boolean): number {
  const base = score >= 75 ? 6 : score >= 50 ? 4 : score >= 25 ? 3 : 2.5;
  return isMajor ? base + 1 : base;
}

export function getStateRiskScore(
  stateName: string,
  constituencies: ConstituencyMPLADS[]
): number | null {
  const stateConsts = constituencies.filter((c) => c.state === stateName);
  if (stateConsts.length === 0) return null;
  return Math.max(...stateConsts.map(computeRiskScore));
}

export function computeNationalStats(constituencies: ConstituencyMPLADS[]) {
  const fundsTrackedCr = constituencies.reduce(
    (sum, c) => sum + c.sanctionedAmount,
    0
  );
  const criticalFlags = constituencies.reduce(
    (sum, c) =>
      sum + c.anomalyFlags.filter((f) => f.severity === "critical").length,
    0
  );
  const elevatedStates = new Set(
    constituencies
      .filter((c) => computeRiskScore(c) >= 50)
      .map((c) => c.state)
  ).size;

  return {
    fundsTrackedCr: Math.round(fundsTrackedCr),
    constituenciesAnalyzed: constituencies.length,
    criticalFlags,
    elevatedStates,
  };
}
