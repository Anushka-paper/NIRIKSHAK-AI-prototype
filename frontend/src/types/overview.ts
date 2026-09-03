/**
 * Type definitions for the complete 6-dataset Overview API.
 */

export interface DatasetSummary {
  id: string;
  name: string;
  description: string;
  records: number;
  columns: number;
  status: "loaded" | "failed";
  error: string | null;
  amount: number;
  qualityScore: number;
  missingValues: number;
  duplicates: number;
}

export interface StateRecord {
  state: string;
  records: number;
}

export interface CategoryRecord {
  category: string;
  records: number;
}

export interface StateSummary {
  id: string;
  name: string;
  type: "STATE" | "UT";
  mpCount?: number;
  rank?: number;
  totalStates?: number;
  totalProjects: number;
  completedProjects: number;
  worksCompleted?: number;
  ongoingProjects: number;
  pendingProjects: number;
  recommendedAmount: number;
  sanctionedAmount: number;
  allocated?: number;
  expenditureAmount: number;
  recordedExpenditure?: number;
  completedAmount: number;
  utilizationRate: number;
  expenditureRate?: number;
  completionRate: number;
}

export interface OverviewData {
  parliament_scope: string;
  datasets: {
    total: number;
    loaded: number;
    failed: number;
    summaries: DatasetSummary[];
  };
  records: {
    total: number;
    totalUniqueWorks: number;
    byDataset: DatasetSummary[];
  };
  projectStatusMetrics?: {
    totalWorks: number;
    completedWorks: number;
    ongoingWorks: number;
    pendingWorks: number;
    completionPercentage: number;
    completedAmount: number;
  };
  features: {
    totalRawColumns: number;
    totalEngineeredFeatures: number;
  };
  dataQuality: {
    score: number;
    missingValues: number;
    duplicates: number;
    validationErrors: number;
    validationStatus: string;
  };
  analytics: {
    totalAllocatedAmount: number;
    totalCalamityAmount: number;
    totalRecommendedAmount: number;
    totalSanctionedAmount: number;
    totalExpenditureAmount: number;
    totalCompletedAmount: number;
    unspentBalance: number;
  };
  geography: {
    topStates: StateRecord[];
    totalStatesRepresented: number;
  };
  categories: CategoryRecord[];
  pipeline: {
    lastUpdated: string | null;
    processingTimeSeconds: number;
  };
}

