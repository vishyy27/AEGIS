"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Target } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface Signal {
  name: string;
  contribution: number;
  max: number;
  description: string;
}

interface ConfidenceData {
  total_confidence: number;
  signals: Signal[];
  penalties: { anomaly_penalty: number; cold_start_penalty: number };
}

export default function ConfidenceBreakdown({ deploymentId }: { deploymentId: number }) {
  const [data, setData] = useState<ConfidenceData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<ConfidenceData>(`/api/xai/confidence/${deploymentId}`)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [deploymentId]);

  if (loading || !data) {
    return <div className="aegis-card animate-pulse"><div className="h-48 bg-slate-800/50 rounded-lg" /></div>;
  }

  const pct = Math.round(data.total_confidence * 100);
  const color = pct >= 70 ? "text-emerald-400" : pct >= 45 ? "text-amber-400" : "text-red-400";
  const ringColor = pct >= 70 ? "#10b981" : pct >= 45 ? "#f59e0b" : "#ef4444";

  return (
    <div className="aegis-card">
      <div className="flex items-center gap-2 mb-6">
        <Target size={18} className="text-cyan-400" />
        <h3 className="section-title">Confidence Breakdown</h3>
      </div>

      {/* Confidence ring */}
      <div className="flex items-center justify-center mb-6">
        <div className="relative w-28 h-28">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            <circle cx="50" cy="50" r="42" fill="none" stroke="#1e293b" strokeWidth="6" />
            <motion.circle
              cx="50" cy="50" r="42" fill="none" stroke={ringColor} strokeWidth="6"
              strokeLinecap="round" strokeDasharray={`${pct * 2.64} 264`}
              initial={{ strokeDasharray: "0 264" }}
              animate={{ strokeDasharray: `${pct * 2.64} 264` }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-2xl font-bold mono ${color}`}>{pct}%</span>
          </div>
        </div>
      </div>

      {/* Signal bars */}
      <div className="space-y-3">
        {data.signals.map((signal, i) => {
          const fillPct = Math.round((signal.contribution / signal.max) * 100);
          return (
            <motion.div key={signal.name} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">{signal.name}</span>
                <span className="text-slate-500 mono">{(signal.contribution * 100).toFixed(0)}%</span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${fillPct}%` }}
                  transition={{ duration: 0.8, delay: i * 0.1 }}
                />
              </div>
              <p className="text-[10px] text-slate-600 mt-0.5">{signal.description}</p>
            </motion.div>
          );
        })}
      </div>

      {/* Penalties */}
      {(data.penalties.anomaly_penalty > 0 || data.penalties.cold_start_penalty > 0) && (
        <div className="mt-4 pt-3 border-t border-slate-800">
          <span className="text-xs text-slate-500 font-medium">Penalties Applied:</span>
          <div className="flex gap-3 mt-1">
            {data.penalties.anomaly_penalty > 0 && (
              <span className="text-xs text-red-400 bg-red-500/10 px-2 py-0.5 rounded">Anomaly: -{(data.penalties.anomaly_penalty * 100).toFixed(0)}%</span>
            )}
            {data.penalties.cold_start_penalty > 0 && (
              <span className="text-xs text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">Cold Start: -{(data.penalties.cold_start_penalty * 100).toFixed(0)}%</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
