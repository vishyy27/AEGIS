"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

// ✅ Props type
type Props = {
  data: number[];
};

// 🎨 Color logic
const getBarColor = (value: number) => {
  if (value > 70) return "#ef4444"; // Red
  if (value > 30) return "#f59e0b"; // Orange
  return "#06b6d4"; // Cyan
};

export default function RiskChart({ data }: Props) {
  // ✅ Convert backend array → chart format
  const chartData = (data || []).map((value, index) => ({
    time: `${index * 2}:00`, // simple time labels
    risk: value,
  }));

  return (
    <div className="aegis-card h-[280px] flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-medium text-slate-200">
          24-Hour Risk Trend
        </h3>
        <span className="text-xs text-slate-500 font-medium bg-slate-800/50 px-2 py-1 rounded">
          Last update: 5m ago
        </span>
      </div>

      <div className="flex-1 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 0, right: 0, left: -25, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="#1e293b"
            />

            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#475569", fontSize: 10 }}
              dy={10}
            />

            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#475569", fontSize: 10 }}
            />

            <Tooltip
              cursor={{ fill: "#1e293b", opacity: 0.4 }}
              contentStyle={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "8px",
                fontSize: "12px",
                color: "#fff",
              }}
            />

            <Bar dataKey="risk" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.risk)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
