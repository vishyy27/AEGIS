"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, X, AlertTriangle } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface WaterfallStage {
  stage: number; name: string; result: string; decision_after: string; description: string;
}

const resultStyle: Record<string, { color: string; icon: React.ReactNode }> = {
  PASS: { color: "text-emerald-400", icon: <Check size={12} /> },
  BLOCK: { color: "text-rose-400", icon: <X size={12} /> },
  WARN: { color: "text-amber-400", icon: <AlertTriangle size={12} /> },
  ESCALATE: { color: "text-orange-400", icon: <AlertTriangle size={12} /> },
  ALLOW: { color: "text-emerald-400", icon: <Check size={12} /> },
};

export default function PolicyWaterfall({ deploymentId }: { deploymentId: number }) {
  const [stages, setStages] = useState<WaterfallStage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<WaterfallStage[]>(`/api/xai/waterfall/${deploymentId}`)
      .then(setStages)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [deploymentId]);

  if (loading) return <div className="aegis-card"><div className="space-y-2">{[1,2,3,4].map(i => <div key={i} className="h-12 bg-[#151a2e] rounded-md animate-pulse" />)}</div></div>;

  return (
    <div className="aegis-card">
      <h3 className="section-title mb-3">Policy Waterfall</h3>
      <div className="space-y-1">
        {stages.map((s, i) => {
          const cfg = resultStyle[s.result] || { color: "text-[#6b7280]", icon: null };
          return (
            <motion.div key={s.stage} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}
              className="flex items-center gap-3 px-3 py-2.5 rounded-md bg-[#0a0e1a] border border-[#1c2333] hover:border-[#232b3e] transition-colors">
              <span className="text-[10px] font-semibold text-[#3d4454] mono w-4 shrink-0">{s.stage}</span>
              <div className="flex-1 min-w-0">
                <span className="text-[12px] text-[#c8cdd8]">{s.name}</span>
                <p className="text-[10px] text-[#4a5468] truncate">{s.description}</p>
              </div>
              <div className={`flex items-center gap-1 ${cfg.color} text-[11px] font-medium shrink-0`}>
                {cfg.icon}
                {s.result}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
