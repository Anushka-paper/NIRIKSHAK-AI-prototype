/**
 * TypeScript Interfaces for NIRIKSHAK-AI Feature Engineering Store.
 */

export interface FeatureCatalogItem {
  feature_name: string;
  feature_group: string;
  data_type: string;
  aggregation_level: string;
  missing_percentage: number;
  unique_count: number;
  min?: number | null;
  max?: number | null;
  mean?: number | null;
  std?: number | null;
  leakage_status: "AVAILABLE_AT_PREDICTION" | "POST_PREDICTION" | "IDENTIFIER";
}

export interface WorkFeature {
  canonical_work_id: string;
  official_work_id?: string;
  parliament: string;
  state: string;
  constituency: string;
  mp_name: string;
  ida_agency?: string;
  work_category?: string;
  work_description?: string;
  recommended_amount?: number;
  sanctioned_amount?: number;
  expenditure_amount?: number;
  completion_amount?: number;
  unspent_amount?: number;
  expenditure_to_sanction_ratio?: number;
  recommendation_to_sanction_amount_change_pct?: number;
  sanction_financial_year?: string;
  sanction_to_completion_days?: number;
  recommendation_to_sanction_days?: number;
  lifecycle_status: string;
  lifecycle_completion_percentage?: number;
  valid_lifecycle_sequence?: number;
  work_description_word_count?: number;
  mp_historical_work_count?: number;
  mp_historical_completion_rate?: number;
  amount_z_score?: number;
  amount_iqr_outlier_flag?: number;
  duration_iqr_outlier_flag?: number;
  has_official_work_id?: number;
  entity_resolution_score?: number;
  entity_resolution_confidence?: string;
  [key: string]: unknown;
}

export interface DimensionAggregations {
  parliament: string;
  mps: Array<{
    mp_name: string;
    state: string;
    work_count: number;
    completed_work_count: number;
    completion_rate: number;
    total_sanctioned_amount: number;
    total_expenditure: number;
  }>;
  constituencies: Array<{
    constituency: string;
    state: string;
    work_count: number;
    completed_work_count: number;
    completion_rate: number;
    total_sanctioned_amount: number;
    total_expenditure: number;
  }>;
  states: Array<{
    state: string;
    work_count: number;
    completed_work_count: number;
    completion_rate: number;
    total_sanctioned_amount: number;
    total_expenditure: number;
  }>;
  vendors: Array<{
    vendor_name: string;
    work_count: number;
    completed_work_count: number;
    completion_rate: number;
    total_expenditure: number;
  }>;
}

export interface FeatureQualityAudit {
  parliament: string;
  summary: {
    total_works_processed?: number;
    total_features_generated?: number;
    total_transactions?: number;
    total_mps?: number;
    elapsed_seconds?: number;
    timestamp?: string;
  };
  quality_audit: Array<{
    feature_name: string;
    quality_status: "HEALTHY" | "WARNING";
    missing_percentage: number;
    unique_count: number;
    is_constant: number;
    has_infinite: number;
    audit_notes: string;
  }>;
  leakage_audit: Array<{
    feature_name: string;
    prediction_milestone: string;
    leakage_status: "AVAILABLE_AT_PREDICTION" | "POST_PREDICTION" | "IDENTIFIER";
    rationale: string;
  }>;
}

