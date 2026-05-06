"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchAPI } from "@/lib/api";

interface HeatmapCell {
  service: string; risk_score: number; decision: string | null;
  timestamp: string; day: string; hour: number;
}

const riskColor = (score: number): string => {
  if (score >= 70) return "#ef4444";
  if (score >= 50) return "#f59e0b";
  if (score >= 30) return "#eab308";
  return "#22c55e";
};

export default function RiskHeatmap() {
  const [data, setData] = useState<HeatmapCell[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<HeatmapCell[]>("/api/fleet/heatmap?days=14")
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="aegis-card"><div className="h-32 bg-[#151a2e] rounded-md animate-pulse" /></div>;

  const services = [...new Set(data.map(d => d.service))];
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <div className="aegis-card">
      <h3 className="section-title mb-4">Risk Heatmap</h3>

      {services.length === 0 ? (
        <p className="text-[12px] text-[#3d4454] text-center py-8">No deployment data available</p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <div className="grid gap-[3px]" style={{ gridTemplateColumns: `100px repeat(${days.length}, 1fr)`, minWidth: "400px" }}>
              <div />
              {days.map(d => (
                <div key={d} className="text-[10px] text-[#4a5468] text-center font-medium py-1">{d}</div>
              ))}

              {services.slice(0, 8).map((service, si) => (
                <React.Fragment key={service}>
                  <div className="text-[11px] text-[#6b7280] truncate pr-2 flex items-center">{service}</div>
                  {days.map((day, di) => {
                    const cell = data.find(d => d.service === service && d.day === day);
                    const score = cell?.risk_score || 0;
                    return (
                      <motion.div
                        key={`${service}-${day}`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: (si * 7 + di) * 0.015 }}
                        className="h-7 rounded-[3px] cursor-default transition-all hover:ring-1 hover:ring-white/10"
                        style={{ backgroundColor: score > 0 ? riskColor(score) : "#151a2e", opacity: score > 0 ? Math.max(0.25, score / 100) : 1 }}
                        title={cell ? `${service}: ${score.toFixed(1)}%` : "No data"}
                      />
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4 mt-3 justify-end">
            {[{ c: "#22c55e", l: "Low" }, { c: "#eab308", l: "Med" }, { c: "#f59e0b", l: "High" }, { c: "#ef4444", l: "Crit" }].map(({ c, l }) => (
              <div key={l} className="flex items-center gap-1">
                <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: c, opacity: 0.7 }} />
                <span className="text-[9px] text-[#4a5468]">{l}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
