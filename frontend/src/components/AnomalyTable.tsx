"use client";

import React, { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle, AlertOctagon } from "lucide-react";

interface AnomalyData {
  state: string;
  critical_anomalies: number;
}

export default function AnomalyTable({ parliament = "all" }: { parliament?: string }) {
  const [data, setData] = useState<AnomalyData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchAnomalies = async () => {
      setLoading(true);
      setError(false);
      try {
        const res = await fetch(`/api/ml/anomalies-by-state?parliament=${parliament}`);
        if (res.ok) {
          const json = await res.json();
          setData(json.data || []);
        } else {
          setError(true);
        }
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    fetchAnomalies();
  }, [parliament]);

  if (loading) return <div className="p-6 text-gray-400 animate-pulse text-sm">Loading anomaly data...</div>;
  if (error) return <div className="p-6 text-red-500 text-sm font-medium">Failed to load anomaly data. Check backend connection.</div>;

  return (
    <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
      <h2 className="text-xl font-bold mb-4 text-gray-800 flex items-center gap-2">
        <AlertTriangle className="text-amber-500" />
        Critical Anomalies by State
      </h2>
      <div className="overflow-x-auto">
        {data.length === 0 ? (
          <p className="text-gray-400 text-sm py-4">No critical anomalies found.</p>
        ) : (
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 text-gray-600 text-sm uppercase tracking-wider border-b">
              <th className="p-3 font-semibold">State</th>
              <th className="p-3 font-semibold">Critical Count</th>
              <th className="p-3 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 text-gray-700">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50 transition-colors">
                <td className="p-3 font-medium">{row.state}</td>
                <td className="p-3 font-mono font-bold">{row.critical_anomalies}</td>
                <td className="p-3">
                  {row.critical_anomalies > 10 ? (
                    <span className="flex items-center gap-1 text-red-600 bg-red-50 px-2 py-1 rounded-full text-xs font-bold w-fit">
                      <AlertOctagon size={14} /> High Risk
                    </span>
                  ) : row.critical_anomalies > 0 ? (
                    <span className="flex items-center gap-1 text-amber-600 bg-amber-50 px-2 py-1 rounded-full text-xs font-bold w-fit">
                      <AlertTriangle size={14} /> Investigate
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-green-600 bg-green-50 px-2 py-1 rounded-full text-xs font-bold w-fit">
                      <CheckCircle size={14} /> Clear
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        )}
      </div>
    </div>
  );
}
