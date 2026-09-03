"use client";

import React, { useState, useEffect } from "react";
import { FeatureCatalogItem } from "@/types/features";
import { fetchFeatureCatalog } from "@/lib/featureService";
import { BookOpen, Search, ShieldCheck, AlertTriangle, Layers, X } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  parliament: string;
}

export default function FeatureCatalogModal({ isOpen, onClose, parliament }: Props) {
  const [catalog, setCatalog] = useState<FeatureCatalogItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterGroup, setFilterGroup] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetchFeatureCatalog(parliament)
        .then((res) => setCatalog(res.catalog))
        .catch((err) => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [isOpen, parliament]);

  if (!isOpen) return null;

  const groups = ["ALL", ...Array.from(new Set(catalog.map((c) => c.feature_group)))];

  const filtered = catalog.filter((item) => {
    const matchGroup = filterGroup === "ALL" || item.feature_group === filterGroup;
    const matchSearch = item.feature_name.toLowerCase().includes(search.toLowerCase());
    return matchGroup && matchSearch;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] flex flex-col shadow-2xl border overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gray-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-headline font-bold text-gray-900">
                NIRIKSHAK Feature Catalog & Dictionary
              </h2>
              <p className="text-xs text-gray-500">
                Showing all 118 engineered ML features for {parliament.toUpperCase().replace("_", " ")}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-200 text-gray-500 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Controls */}
        <div className="p-6 border-b flex flex-col sm:flex-row gap-4 justify-between bg-white">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search feature by name (e.g. expenditure_to_sanction_ratio)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:border-primary"
            />
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
            <Layers className="w-4 h-4 text-gray-400" />
            <select
              value={filterGroup}
              onChange={(e) => setFilterGroup(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary bg-white"
            >
              {groups.map((g) => (
                <option key={g} value={g}>
                  {g.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Catalog Table */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="py-20 text-center text-gray-400 text-sm">Loading feature metadata...</div>
          ) : filtered.length === 0 ? (
            <div className="py-20 text-center text-gray-400 text-sm">No features matching your filters.</div>
          ) : (
            <div className="border rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 text-xs font-bold uppercase text-gray-500 border-b">
                  <tr>
                    <th className="p-3">Feature Name</th>
                    <th className="p-3">Group</th>
                    <th className="p-3">Data Type</th>
                    <th className="p-3">Missing %</th>
                    <th className="p-3">Leakage Classification</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filtered.map((item) => (
                    <tr key={item.feature_name} className="hover:bg-gray-50/80 transition-colors">
                      <td className="p-3 font-mono font-medium text-xs text-gray-900">
                        {item.feature_name}
                      </td>
                      <td className="p-3 text-xs">
                        <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-semibold text-[10px]">
                          {item.feature_group}
                        </span>
                      </td>
                      <td className="p-3 text-xs font-mono text-gray-600">{item.data_type}</td>
                      <td className="p-3 text-xs">
                        <span
                          className={`font-semibold ${
                            item.missing_percentage > 50 ? "text-amber-600" : "text-gray-700"
                          }`}
                        >
                          {item.missing_percentage}%
                        </span>
                      </td>
                      <td className="p-3 text-xs">
                        {item.leakage_status === "AVAILABLE_AT_PREDICTION" ? (
                          <span className="inline-flex items-center gap-1 text-green-700 bg-green-50 px-2 py-0.5 rounded-full font-bold text-[10px]">
                            <ShieldCheck className="w-3 h-3" /> PRE-SANCTION SAFE
                          </span>
                        ) : item.leakage_status === "POST_PREDICTION" ? (
                          <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full font-bold text-[10px]">
                            <AlertTriangle className="w-3 h-3" /> POST-PREDICTION / OUTCOME
                          </span>
                        ) : (
                          <span className="text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full font-bold text-[10px]">
                            IDENTIFIER
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

