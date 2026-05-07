"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle2, Sparkles, BrainCircuit, ShieldAlert, ArrowRight, Activity } from "lucide-react";
import { useGlobalWebSocket } from "@/providers/WebSocketProvider";
import { motion, AnimatePresence } from "framer-motion";

interface ActionableRec {
  id: string;
  type: "SECURITY" | "PERFORMANCE" | "STABILITY";
  message: string;
  impact: string;
  urgency: "HIGH" | "MEDIUM" | "LOW";
}

const mockRecs: ActionableRec[] = [
  { id: "1", type: "SECURITY", message: "Rotate IAM keys for production-k8s cluster", impact: "High risk of credential leak", urgency: "HIGH" },
  { id: "2", type: "PERFORMANCE", message: "Scale cache nodes by +2 units in us-east-1", impact: "Reduce P99 latency by 40ms", urgency: "MEDIUM" },
  { id: "3", type: "STABILITY", message: "Revert PR #4092 due to memory leak signatures", impact: "Prevent out-of-memory crashes", urgency: "HIGH" }
];

export default function RecommendationPanel() {
  const { isConnected } = useGlobalWebSocket();
  const [recs, setRecs] = useState<ActionableRec[]>([]);
  const [analyzing, setAnalyzing] = useState(true);

  useEffect(() => {
    // Simulate initial AI analysis
    const t = setTimeout(() => {
      setRecs(mockRecs);
      setAnalyzing(false);
    }, 1500);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="aegis-card h-full flex flex-col relative overflow-hidden">
      {/* Background AI FX */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-900/10 to-transparent blur-2xl pointer-events-none" />

      <div className="flex items-center justify-between mb-4 relative z-10">
        <div>
          <h3 className="section-title text-blue-400 flex items-center gap-1.5">
            <Sparkles size={13} className="animate-pulse" />
            AI Copilot Insights
          </h3>
          <span className="text-[10px] text-[#4a5468] block mt-0.5">Real-time operational analysis</span>
        </div>
        
        {analyzing ? (
          <div className="flex items-center gap-1.5 text-[10px] text-[#8892a8] bg-[#151a2e] px-2 py-1 rounded-md border border-[#1c2333]">
            <BrainCircuit size={10} className="animate-spin text-blue-400" />
            Evaluating Fleet...
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-md border border-emerald-500/20">
            <CheckCircle2 size={10} />
            Optimized
          </div>
        )}
      </div>

      <div className="flex-1 space-y-2 relative z-10">
        <AnimatePresence>
          {analyzing ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center justify-center h-32 text-[#4a5468]">
              <Activity size={24} className="mb-2 animate-pulse text-[#232b3e]" />
              <div className="text-[11px] mono">Synthesizing telemetry...</div>
            </motion.div>
          ) : (
            recs.map((rec, i) => (
              <motion.div 
                key={rec.id}
                initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}
                className="group flex flex-col gap-1 p-3 bg-[#0a0e1a] rounded-md border border-[#1c2333] hover:border-blue-500/30 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    {rec.urgency === "HIGH" ? (
                      <ShieldAlert size={12} className="text-rose-400 shrink-0" />
                    ) : (
                      <BrainCircuit size={12} className="text-blue-400 shrink-0" />
                    )}
                    <span className={`text-[12px] font-medium ${rec.urgency === "HIGH" ? "text-[#e2e8f0]" : "text-[#c8cdd8]"}`}>
                      {rec.message}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mt-1.5 ml-4.5">
                  <span className="text-[10px] text-[#6b7280]">
                    Impact: <span className="text-[#8892a8]">{rec.impact}</span>
                  </span>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-[10px] text-blue-400 font-medium">
                    Apply <ArrowRight size={10} />
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {!analyzing && (
        <div className="mt-4 pt-3 border-t border-[#1c2333] flex justify-between items-center text-[10px] text-[#4a5468] relative z-10">
          <span>Based on 2.4B events</span>
          <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" /> Live</span>
        </div>
      )}
    </div>
  );
}
