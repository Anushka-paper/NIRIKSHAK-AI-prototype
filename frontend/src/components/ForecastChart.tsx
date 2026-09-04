"use client";

import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart
} from "recharts";
import { TrendingUp } from "lucide-react";

export default function ForecastChart({ entityId = "ALL" }: { entityId?: string }) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchForecast = async () => {
      setLoading(true);
      setError(false);
      try {
        const res = await fetch(`/api/ml/forecast/${entityId}`);
        if (res.ok) {
          const json = await res.json();
          setData(Array.isArray(json) ? json : []);
        } else {
          setError(true);
        }
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    fetchForecast();
  }, [entityId]);

  if (loading) return <div className="p-6 text-gray-400 animate-pulse text-sm">Computing 6-month forecast...</div>;
  if (error || data.length === 0) return <div className="p-6 text-red-400 text-sm font-medium">Forecast unavailable. Backend may still be loading.</div>;

  return (
    <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
      <h2 className="text-xl font-bold mb-1 text-gray-800 flex items-center gap-2">
        <TrendingUp className="text-blue-500" />
        6-Month Expenditure Forecast
      </h2>
      <p className="text-xs text-gray-400 mb-5">Forward projection from {data[0]?.ds} to {data[data.length - 1]?.ds} &bull; Confidence band shown</p>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
            <XAxis dataKey="ds" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} tickFormatter={(val) => `₹${(val/100000).toFixed(1)}L`} />
            <Tooltip 
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              formatter={(value: any) => [`₹${Number(value).toLocaleString()}`, '']}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            
            {/* Confidence Interval Area */}
            <Area 
              type="monotone" 
              dataKey="yhat_upper" 
              stroke="none" 
              fill="#bfdbfe" 
              fillOpacity={0.4} 
              name="Upper Bound"
            />
            <Area 
              type="monotone" 
              dataKey="yhat_lower" 
              stroke="none" 
              fill="#ffffff" 
              fillOpacity={1} 
              name="Lower Bound"
            />
            
            {/* Main Prediction Line */}
            <Line 
              type="monotone" 
              dataKey="yhat" 
              stroke="#3b82f6" 
              strokeWidth={3} 
              dot={{ r: 4, strokeWidth: 2 }} 
              activeDot={{ r: 6 }} 
              name="Forecasted Amount"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
