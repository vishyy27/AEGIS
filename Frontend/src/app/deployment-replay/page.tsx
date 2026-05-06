"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Play } from "lucide-react";
import { fetchAPI } from "@/lib/api";
import ReplayTimeline from "@/components/ReplayTimeline";

interface ReplayEntry {
  deployment_id: number; service: string; risk_score: number;
  risk_level: string; decision: string; event_count: number;
  alert_count: number; timestamp: string;
}

const decisionColor: Record<string, string> = {
  BLOCK: "text-rose-400", WARN: "text-amber-400", ALLOW: "text-emerald-400",
};

export default function DeploymentReplayPage() {
  const [entries, setEntries] = useState<ReplayEntry[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<ReplayEntry[]>("/api/replay/list?limit=25")
      .then(setEntries)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">Deployment Replay</h1>
        <p className="text-muted mt-0.5">Replay historical deployments to analyze decision timelines</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4" style={{ height: "calc(100vh - 180px)" }}>
        {/* List */}
        <div className="aegis-card lg:col-span-1 flex flex-col overflow-hidden">
          <h3 className="section-title mb-3 shrink-0">Deployments</h3>
          {loading ? (
            <div className="space-y-2">{[1,2,3,4].map(i => <div key={i} className="h-14 bg-[#151a2e] rounded-md animate-pulse" />)}</div>
          ) : (
            <div className="space-y-1 overflow-y-auto flex-1">
              {entries.map((e, i) => (
                <motion.button key={e.deployment_id} onClick={() => setSelected(e.deployment_id)}
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.02 }}
                  className={`w-full text-left px-3 py-2.5 rounded-md transition-all border ${
                    selected === e.deployment_id ? "bg-blue-500/8 border-blue-500/15" : "border-transparent hover:bg-white/[0.02]"
                  }`}>
                  <div className="flex justify-between items-center">
                    <span className="text-[12px] font-medium text-[#c8cdd8] truncate">{e.service || "Unknown"}</span>
                    <span className="text-[11px] mono text-[#6b7280]">{e.risk_score?.toFixed(0)}%</span>
                  </div>
                  <div className="flex gap-2 mt-0.5">
                    <span className="text-[10px] text-[#3d4454]">{e.event_count} events</span>
                    <span className="text-[10px] text-[#3d4454]">{e.alert_count} alerts</span>
                    {e.decision && <span className={`text-[10px] font-medium ${decisionColor[e.decision] || "text-[#4a5468]"}`}>{e.decision}</span>}
                  </div>
                </motion.button>
              ))}
            </div>
          )}
        </div>

        {/* Replay */}
        <div className="lg:col-span-2">
          {selected ? (
            <ReplayTimeline deploymentId={selected} />
          ) : (
            <div className="aegis-card flex flex-col items-center justify-center h-full">
              <Play size={20} className="text-[#232b3e] mb-2" />
              <p className="text-[12px] text-[#3d4454]">Select a deployment to replay</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
