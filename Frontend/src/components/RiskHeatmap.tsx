"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Flame } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface HeatmapCell {
  service: string;
  risk_score: number;
  decision: string | null;
  timestamp: string;
  day: string;
  hour: number;
}

const riskColor = (score: number) => {
  if (score >= 70) return "bg-red-500";
  if (score >= 50) return "bg-orange-500";
  if (score >= 30) return "bg-amber-500";
  return "bg-emerald-500";
};

const riskOpacity = (score: number) => {
  if (score >= 70) return "opacity-90";
  if (score >= 50) return "opacity-70";
  if (score >= 30) return "opacity-50";
  return "opacity-30";
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

  if (loading) {
    return <div className="aegis-card animate-pulse"><div className="h-48 bg-slate-800/50 rounded-lg" /></div>;
  }

  // Group by service
  const services = [...new Set(data.map(d => d.service))];
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <div className="aegis-card">
      <div className="flex items-center gap-2 mb-6">
        <Flame size={18} className="text-orange-400" />
        <h3 className="section-title">Risk Heatmap</h3>
      </div>

      {services.length === 0 ? (
        <p className="text-sm text-slate-500 text-center py-8">No deployment data for heatmap</p>
      ) : (
        <div className="overflow-x-auto">
          <div className="grid gap-1" style={{ gridTemplateColumns: `120px repeat(${days.length}, 1fr)` }}>
            {/* Header */}
            <div />
            {days.map(d => (
              <div key={d} className="text-[10px] text-slate-500 text-center font-medium">{d}</div>
            ))}

            {/* Rows */}
            {services.slice(0, 8).map((service, si) => (
              <React.Fragment key={service}>
                <div className="text-xs text-slate-400 truncate pr-2 flex items-center">{service}</div>
                {days.map((day, di) => {
                  const cell = data.find(d => d.service === service && d.day === day);
                  const score = cell?.risk_score || 0;
                  return (
                    <motion.div
                      key={`${service}-${day}`}
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: (si * 7 + di) * 0.02 }}
                      className={`h-8 rounded ${score > 0 ? `${riskColor(score)} ${riskOpacity(score)}` : "bg-slate-800/30"} cursor-pointer hover:ring-1 hover:ring-white/20 transition-all`}
                      title={cell ? `${service}: ${score.toFixed(1)} risk` : "No data"}
                    />
                  );
                })}
              </React.Fragment>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 mt-4 justify-center">
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-emerald-500 opacity-30" /><span className="text-[10px] text-slate-500">Low</span></div>
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-amber-500 opacity-50" /><span className="text-[10px] text-slate-500">Medium</span></div>
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-orange-500 opacity-70" /><span className="text-[10px] text-slate-500">High</span></div>
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-red-500 opacity-90" /><span className="text-[10px] text-slate-500">Critical</span></div>
          </div>
        </div>
      )}
    </div>
  );
}
