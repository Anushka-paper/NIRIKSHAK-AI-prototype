"use client";

import React, { useState, useEffect } from "react";
import { WorkFeature } from "@/types/features";
import { fetchWorkFeatures } from "@/lib/featureService";
import { Search, Filter, ChevronLeft, ChevronRight, RefreshCw, LayoutGrid, List } from "lucide-react";
import WorkFeatureDetailModal from "./WorkFeatureDetailModal";
import ProjectCard from "./ProjectCard";

interface Props {
  parliament: string;
}

export default function FeatureWorkTable({ parliament }: Props) {
  const [works, setWorks] = useState<WorkFeature[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedWork, setSelectedWork] = useState<WorkFeature | null>(null);

  const limit = 24;

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetchWorkFeatures({
        parliament,
        search: search || undefined,
        lifecycle_status: statusFilter === "ALL" ? undefined : statusFilter,
        risk_level: riskFilter === "ALL" ? undefined : riskFilter,
        limit,
        offset: page * limit,
      });
      setWorks(res.records);
      setTotalCount(res.total_count);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(0);
  }, [parliament, statusFilter, riskFilter, search]);

  useEffect(() => {
    loadData();
  }, [parliament, page, statusFilter, riskFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    loadData();
  };

  const formatCurrency = (val?: number) => {
    if (!val) return "₹0";
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    return `₹${val.toLocaleString()}`;
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Search, Filter & View Controls */}
      <div className="p-4 bg-white rounded-2xl border shadow-subtle flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Canonical ID, Description, MP, or Constituency..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border rounded-xl text-sm focus:outline-none focus:border-primary bg-white"
          />
        </form>

        <div className="flex items-center gap-2 w-full md:w-auto">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 border rounded-xl px-2.5 py-1.5 bg-white">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs font-semibold focus:outline-none bg-transparent text-gray-700"
            >
              <option value="ALL">All Statuses</option>
              <option value="COMPLETED">Completed</option>
              <option value="EXPENDITURE_STARTED">Expenditure Started</option>
              <option value="SANCTIONED">Sanctioned</option>
              <option value="RECOMMENDED_ONLY">Recommended Only</option>
            </select>
          </div>

          {/* Risk Filter */}
          <div className="flex items-center gap-1.5 border rounded-xl px-2.5 py-1.5 bg-white">
            <Filter className="w-4 h-4 text-red-400" />
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="text-xs font-semibold focus:outline-none bg-transparent text-gray-700"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="ALL_ANOMALIES">All Flagged Anomalies</option>
              <option value="CRITICAL_RISK">Critical Risk (&ge; 85%)</option>
              <option value="HIGH_RISK">High Risk (70-84%)</option>
              <option value="MEDIUM_RISK">Medium Risk (50-69%)</option>
              <option value="LOW_RISK">Low Risk (&lt; 50%)</option>
            </select>
          </div>

          {/* View Mode Toggle: Cards vs Table */}
          <div className="bg-gray-100 p-1 rounded-xl flex items-center">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
                viewMode === "grid"
                  ? "bg-white text-primary shadow-sm"
                  : "text-gray-500 hover:text-gray-900"
              }`}
              title="Card Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={`p-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
                viewMode === "table"
                  ? "bg-white text-primary shadow-sm"
                  : "text-gray-500 hover:text-gray-900"
              }`}
              title="Table View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={loadData}
            className="p-2 rounded-xl border hover:bg-gray-100 text-gray-600 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Content Rendering: Card Grid or Table */}
      {loading ? (
        <div className="py-24 text-center text-gray-400 bg-white rounded-2xl border">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-primary opacity-50" />
          <p className="text-sm font-medium">Loading project cards from ML service...</p>
        </div>
      ) : works.length === 0 ? (
        <div className="py-24 text-center text-gray-400 bg-white rounded-2xl border">
          <p className="text-base font-semibold text-gray-700">No project records found</p>
          <p className="text-xs mt-1">Try adjusting your search keywords or filter status.</p>
        </div>
      ) : viewMode === "grid" ? (
        /* Separate Card for Each Project */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {works.map((w) => (
            <ProjectCard
              key={w.canonical_work_id}
              work={w}
              onViewDetails={(selected) => setSelectedWork(selected)}
            />
          ))}
        </div>
      ) : (
        /* Table View */
        <div className="bg-white rounded-2xl border shadow-subtle overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs font-bold uppercase text-gray-500 border-b">
                <tr>
                  <th className="p-3">Canonical ID</th>
                  <th className="p-3">State / Constituency</th>
                  <th className="p-3">Sanctioned (₹)</th>
                  <th className="p-3">Expenditure (₹)</th>
                  <th className="p-3">Utilization</th>
                  <th className="p-3">Lifecycle Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {works.map((w) => (
                  <tr key={w.canonical_work_id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="p-3 font-mono font-medium text-xs text-primary">
                      {w.canonical_work_id}
                    </td>
                    <td className="p-3">
                      <span className="font-bold text-gray-900 block text-xs">{w.state}</span>
                      <span className="text-[11px] text-gray-500">{w.constituency}</span>
                    </td>
                    <td className="p-3 font-bold text-gray-800 text-xs">
                      {formatCurrency(w.sanctioned_amount)}
                    </td>
                    <td className="p-3 font-bold text-secondary text-xs">
                      {formatCurrency(w.expenditure_amount)}
                    </td>
                    <td className="p-3 text-xs">
                      <span
                        className={`font-semibold ${
                          (w.expenditure_to_sanction_ratio || 0) > 1.0
                            ? "text-red-600"
                            : "text-gray-700"
                        }`}
                      >
                        {((w.expenditure_to_sanction_ratio || 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="p-3 text-xs">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          w.lifecycle_status === "COMPLETED"
                            ? "bg-green-100 text-green-800"
                            : w.lifecycle_status === "EXPENDITURE_STARTED"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        {w.lifecycle_status}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => setSelectedWork(w)}
                        className="px-3 py-1.5 rounded-lg border hover:bg-primary hover:text-white text-xs font-semibold text-gray-700 transition-colors inline-flex items-center gap-1.5"
                      >
                        View Features
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination Footer */}
      <div className="p-4 bg-white rounded-2xl border shadow-subtle flex items-center justify-between text-xs text-gray-500">
        <div>
          Showing <span className="font-bold text-gray-800">{works.length}</span> of{" "}
          <span className="font-bold text-gray-800">{totalCount.toLocaleString()}</span> works
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0 || loading}
            className="p-1.5 rounded-lg border bg-white disabled:opacity-40 hover:bg-gray-50"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="px-2 font-medium">Page {page + 1}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={(page + 1) * limit >= totalCount || loading}
            className="p-1.5 rounded-lg border bg-white disabled:opacity-40 hover:bg-gray-50"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Detail Modal */}
      <WorkFeatureDetailModal work={selectedWork} onClose={() => setSelectedWork(null)} />
    </div>
  );
}
