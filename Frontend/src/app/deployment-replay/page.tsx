"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Clock, Play } from "lucide-react";
import { fetchAPI } from "@/lib/api";
import ReplayTimeline from "@/components/ReplayTimeline";

interface ReplayEntry {
  deployment_id: number; service: string; risk_score: number;
  risk_level: string; decision: string; outcome: string;
  event_count: number; alert_count: number;
  timestamp: string; has_replay_data: boolean;
}

export default function DeploymentReplayPage() {
  const [entries, setEntries] = useState<ReplayEntry[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<ReplayEntry[]>("/api/replay/list?limit=20")
      .then(setEntries)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title text-gradient-cyan flex items-center gap-3">
          <Clock size={28} className="text-cyan-400" />
          Deployment Replay
        </h1>
        <p className="text-muted mt-1">Replay historical deployments to analyze decision timelines</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Deployment list */}
        <div className="aegis-card lg:col-span-1">
          <h3 className="section-title mb-4">Deployments</h3>
          {loading ? (
            <div className="space-y-2">{[1,2,3,4,5].map(i => <div key={i} className="h-16 bg-slate-800/50 rounded-lg animate-pulse" />)}</div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {entries.map((e, i) => (
                <motion.button key={e.deployment_id} onClick={() => setSelected(e.deployment_id)}
                  initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-all border ${
                    selected === e.deployment_id ? "bg-cyan-500/10 border-cyan-500/20" : "bg-slate-900/30 border-transparent hover:border-slate-700"
                  }`}>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-slate-200 truncate">{e.service || "Unknown"}</span>
                    <span className={`text-[10px] font-bold ${e.risk_level === "HIGH" ? "text-red-400" : e.risk_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400"}`}>
                      {e.risk_score?.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex gap-3 mt-1">
                    <span className="text-[10px] text-slate-500">{e.event_count} events</span>
                    <span className="text-[10px] text-slate-500">{e.alert_count} alerts</span>
                    {e.decision && <span className={`text-[10px] ${e.decision === "BLOCK" ? "text-red-400" : e.decision === "WARN" ? "text-amber-400" : "text-emerald-400"}`}>{e.decision}</span>}
                  </div>
                </motion.button>
              ))}
            </div>
          )}
        </div>

        {/* Replay viewer */}
        <div className="lg:col-span-2">
          {selected ? (
            <ReplayTimeline deploymentId={selected} />
          ) : (
            <div className="aegis-card flex flex-col items-center justify-center py-20">
              <Play size={48} className="text-slate-700 mb-4" />
              <p className="text-sm text-slate-500">Select a deployment to replay its timeline</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
