import { WorkFeature, FeatureCatalogItem, DimensionAggregations, FeatureQualityAudit } from "@/types/features";

export async function fetchFeatureCatalog(parliament: string): Promise<{ catalog: FeatureCatalogItem[] }> {
  const res = await fetch(`/api/features/catalog?parliament=${parliament}`);
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data;
}

export async function fetchDimensionAggregations(parliament: string): Promise<DimensionAggregations> {
  const res = await fetch(`/api/features/aggregations?parliament=${parliament}`);
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data;
}

export async function fetchFeatureQualityAudit(parliament: string): Promise<FeatureQualityAudit> {
  const res = await fetch(`/api/features/quality?parliament=${parliament}`);
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data;
}

export interface FetchWorkFeaturesParams {
  parliament?: string;
  search?: string;
  lifecycle_status?: string;
  risk_level?: string;
  limit?: number;
  offset?: number;
}

export interface FetchWorkFeaturesResponse {
  records: WorkFeature[];
  total_count: number;
}

export async function fetchWorkFeatures(params: FetchWorkFeaturesParams): Promise<FetchWorkFeaturesResponse> {
  const query = new URLSearchParams();
  if (params.parliament) query.append("parliament", params.parliament);
  if (params.search) query.append("search", params.search);
  if (params.lifecycle_status && params.lifecycle_status !== "ALL") {
    query.append("lifecycle_status", params.lifecycle_status);
  }
  if (params.risk_level && params.risk_level !== "ALL") {
    query.append("risk_level", params.risk_level);
  }
  if (params.limit !== undefined) query.append("limit", params.limit.toString());
  if (params.offset !== undefined) query.append("offset", params.offset.toString());

  const res = await fetch(`/api/features/works?${query.toString()}`);
  const json = await res.json();
  if (!json.success) throw new Error(json.error || "Failed to fetch work features");
  return json.data;
}
