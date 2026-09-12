import { OverviewData, StateSummary } from "@/types/overview";

export interface DashboardOverviewResponse {
  success: boolean;
  data: OverviewData;
  error?: string;
}

export interface MLHealthResponse {
  success: boolean;
  data: any;
  error?: string;
}

export async function checkMLHealth(): Promise<MLHealthResponse> {
  const res = await fetch("/api/ml/health");
  return res.json();
}

export async function getDashboardOverview(parliamentScope: string = "all"): Promise<DashboardOverviewResponse> {
  const res = await fetch(`/api/ml/overview?parliament=${parliamentScope}`);
  return res.json();
}

export async function getStateAggregations(parliamentScope: string = "all"): Promise<{ success: boolean, data: StateSummary[] }> {
  const res = await fetch(`/api/overview/states?parliament=${parliamentScope}`);
  return res.json();
}

export async function getSingleStateDetails(stateId: string, parliamentScope: string = "all"): Promise<any> {
  const res = await fetch(`/api/overview/states/${stateId}?parliament=${parliamentScope}`);
  return res.json();
}

export interface PredictionResponse {
  success: boolean;
  data?: any;
  error?: string;
  details?: string;
}

export async function predictRisk(payload: any): Promise<PredictionResponse> {
  const res = await fetch("/api/ml/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ...payload, _t: Date.now() }),
    cache: "no-store"
  });
  return res.json();
}

export interface RiskExplanationResponse {
  success: boolean;
  data?: {
    work_id: string;
    prediction: any;
    why: string[];
    recommended_actions: { action: string; rationale: string }[];
    confidence_note: string;
    generated_by: "llm" | "fallback";
    cached: boolean;
  };
  error?: string;
}

export async function getRiskExplanation(workId: string): Promise<RiskExplanationResponse> {
  const res = await fetch(`/api/ml/risk-explanation/${encodeURIComponent(workId)}`, { cache: "no-store" });
  return res.json();
}

export async function checkDuplicate(query: string): Promise<any> {
  const res = await fetch("/api/nlp/check-duplicate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });
  return res.json();
}
