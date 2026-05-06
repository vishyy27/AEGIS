"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchAPI } from "@/lib/api";

interface Signal { name: string; contribution: number; max: number; description: string; }
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

  if (loading || !data) return <div className="aegis-card"><div className="h-40 bg-[#151a2e] rounded-md animate-pulse" /></div>;

  const pct = Math.round(data.total_confidence * 100);
  const color = pct >= 70 ? "text-emerald-400" : pct >= 45 ? "text-amber-400" : "text-rose-400";
  const barColor = pct >= 70 ? "bg-emerald-500" : pct >= 45 ? "bg-amber-500" : "bg-rose-500";

  return (
    <div className="aegis-card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="section-title">Confidence</h3>
        <span className={`text-xl font-semibold mono ${color}`}>{pct}%</span>
      </div>

      {/* Overall bar */}
      <div className="h-1.5 bg-[#1c2333] rounded-full overflow-hidden mb-5">
        <motion.div className={`h-full rounded-full ${barColor}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }} />
      </div>

      {/* Signals */}
      <div className="space-y-3">
        {data.signals.map((sig, i) => {
          const fillPct = Math.round((sig.contribution / sig.max) * 100);
          return (
            <motion.div key={sig.name} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.08 }}>
              <div className="flex justify-between mb-1">
                <span className="text-[11px] text-[#8892a8]">{sig.name}</span>
                <span className="text-[10px] text-[#4a5468] mono">{(sig.contribution * 100).toFixed(0)}%</span>
              </div>
              <div className="h-1 bg-[#1c2333] rounded-full overflow-hidden">
                <motion.div className="h-full rounded-full bg-blue-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${fillPct}%` }}
                  transition={{ duration: 0.6, delay: i * 0.08 }} />
              </div>
              <p className="text-[9px] text-[#3d4454] mt-0.5">{sig.description}</p>
            </motion.div>
          );
        })}
      </div>

      {(data.penalties.anomaly_penalty > 0 || data.penalties.cold_start_penalty > 0) && (
        <div className="mt-4 pt-3 border-t border-[#1c2333] flex gap-2">
          {data.penalties.cold_start_penalty > 0 && (
            <span className="text-[10px] text-amber-400 bg-amber-500/8 px-1.5 py-0.5 rounded">Cold Start: -{(data.penalties.cold_start_penalty * 100).toFixed(0)}%</span>
          )}
          {data.penalties.anomaly_penalty > 0 && (
            <span className="text-[10px] text-rose-400 bg-rose-500/8 px-1.5 py-0.5 rounded">Anomaly: -{(data.penalties.anomaly_penalty * 100).toFixed(0)}%</span>
          )}
        </div>
      )}
    </div>
  );
}
