"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Shield, Check, X, AlertTriangle, ChevronRight } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface WaterfallStage {
  stage: number;
  name: string;
  input: Record<string, unknown>;
  result: string;
  decision_after: string;
  description: string;
}

const resultColors: Record<string, string> = {
  PASS: "text-emerald-400",
  BLOCK: "text-red-400",
  WARN: "text-amber-400",
  ESCALATE: "text-orange-400",
  LOW_CONFIDENCE: "text-violet-400",
  HIGH_CONFIDENCE: "text-emerald-400",
  ALLOW: "text-emerald-400",
};

const resultBgs: Record<string, string> = {
  PASS: "bg-emerald-500/10",
  BLOCK: "bg-red-500/10",
  WARN: "bg-amber-500/10",
  ESCALATE: "bg-orange-500/10",
  ALLOW: "bg-emerald-500/10",
};

const resultIcons: Record<string, React.ReactNode> = {
  PASS: <Check size={14} />,
  BLOCK: <X size={14} />,
  WARN: <AlertTriangle size={14} />,
  ALLOW: <Check size={14} />,
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

  if (loading) {
    return (
      <div className="aegis-card animate-pulse">
        <div className="h-6 w-48 bg-slate-800 rounded mb-4" />
        <div className="space-y-3">
          {[1,2,3,4,5].map(i => <div key={i} className="h-16 bg-slate-800/50 rounded-lg" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="aegis-card">
      <div className="flex items-center gap-2 mb-6">
        <Shield size={18} className="text-cyan-400" />
        <h3 className="section-title">Policy Waterfall</h3>
      </div>

      <div className="space-y-1">
        {stages.map((stage, i) => {
          const color = resultColors[stage.result] || "text-slate-400";
          const bg = resultBgs[stage.result] || "bg-slate-800/30";
          const icon = resultIcons[stage.result] || <ChevronRight size={14} />;

          return (
            <motion.div
              key={stage.stage}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
            >
              <div className={`${bg} rounded-lg px-4 py-3 border border-transparent hover:border-slate-700 transition-colors`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-400 mono">
                      {stage.stage}
                    </span>
                    <span className="text-sm font-medium text-slate-200">{stage.name}</span>
                  </div>
                  <div className={`flex items-center gap-1.5 ${color} text-xs font-semibold`}>
                    {icon}
                    <span>{stage.result}</span>
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-1.5 ml-9">{stage.description}</p>
                {i < stages.length - 1 && (
                  <div className="flex justify-center mt-2">
                    <div className="w-px h-3 bg-slate-700" />
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
