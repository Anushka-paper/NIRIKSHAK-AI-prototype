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

export default function ForecastChart({ entityId = "default" }: { entityId?: string }) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchForecast = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_ML_SERVICE_URL || "http://localhost:8000";
        const res = await fetch(`${baseUrl}/api/forecast/${entityId}`);
        if (res.ok) {
          const json = await res.json();
          setData(json);
        } else {
          setMockData();
        }
      } catch (e) {
        setMockData();
      } finally {
        setLoading(false);
      }
    };

    const setMockData = () => {
      // Generate some mock time series data with bounds if backend is unavailable
      const mock = Array.from({ length: 6 }).map((_, i) => {
        const base = 500000 + i * 50000;
        return {
          ds: `2024-0${i + 1}-01`,
          yhat: base,
          yhat_lower: base - 20000,
          yhat_upper: base + 20000,
        };
      });
      setData(mock);
    };

    fetchForecast();
  }, [entityId]);

  if (loading) return <div className="p-4 text-gray-500 animate-pulse">Loading forecast...</div>;

  return (
    <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
      <h2 className="text-xl font-bold mb-6 text-gray-800 flex items-center gap-2">
        <TrendingUp className="text-blue-500" />
        6-Month Expenditure Forecast (Prophet)
      </h2>
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
