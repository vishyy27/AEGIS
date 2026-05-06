"use client";

import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from "recharts";

type Props = { data: number[] };

const barColor = (v: number) => v > 70 ? "#ef4444" : v > 40 ? "#eab308" : "#3b82f6";

export default function RiskChart({ data }: Props) {
  const chartData = (data || []).map((value, i) => ({
    time: `${i * 2}:00`,
    risk: value,
  }));

  return (
    <div className="aegis-card h-[260px] flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="section-title">24h Risk Trend</h3>
        <span className="text-[10px] text-[#3d4454]">
          {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>

      <div className="flex-1 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 0, right: 0, left: -30, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1c2333" />
            <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: "#3d4454", fontSize: 10 }} dy={8} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: "#3d4454", fontSize: 10 }} />
            <Tooltip
              cursor={{ fill: "#151a2e", opacity: 0.5 }}
              contentStyle={{ backgroundColor: "#0f1422", border: "1px solid #1c2333", borderRadius: "6px", fontSize: "11px", color: "#c8cdd8" }}
            />
            <Bar dataKey="risk" radius={[3, 3, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={`c-${i}`} fill={barColor(entry.risk)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
