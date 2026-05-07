"use client";

import React, { useEffect, useState } from "react";
import { fetchAPI } from "@/lib/api";
import { useGlobalWebSocket } from "@/providers/WebSocketProvider";
import { motion, AnimatePresence } from "framer-motion";
import { GitCommit, Activity, ShieldCheck, ShieldAlert, Shield } from "lucide-react";

interface Deployment {
  id: number;
  repo_name: string;
  environment: string;
  risk_score: number;
  decision: string;
  outcome: string;
  timestamp: string;
}

const decisionStyle: Record<string, { bg: string, text: string, border: string, icon: any }> = {
  ALLOW: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/20", icon: ShieldCheck },
  WARN: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/20", icon: Shield },
  BLOCK: { bg: "bg-rose-500/10", text: "text-rose-400", border: "border-rose-500/20", icon: ShieldAlert },
};

const outcomeStyle: Record<string, string> = {
  success: "text-emerald-400",
  failure: "text-rose-400",
  pending: "text-[#4a5468] animate-pulse",
};

export default function DeploymentTable({ limit = 10 }: { limit?: number }) {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);
  const { lastMessage, subscribe } = useGlobalWebSocket();

  useEffect(() => {
    fetchAPI<Deployment[]>(`/api/deployments/?limit=${limit}`)
      .then(setDeployments)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [limit]);

  useEffect(() => {
    subscribe(["deployments"]);
  }, [subscribe]);

  useEffect(() => {
    if (lastMessage?.type === "deployment_update" && lastMessage.data) {
      const eventData = lastMessage.data as Deployment;
      setDeployments(prev => {
        const exists = prev.findIndex(d => d.id === eventData.id);
        if (exists !== -1) {
          const copy = [...prev];
          copy[exists] = { ...copy[exists], ...eventData };
          return copy;
        }
        return [eventData, ...prev].slice(0, limit);
      });
    }
  }, [lastMessage, limit]);

  if (loading) {
    return (
      <div className="space-y-1">
        {Array.from({ length: Math.min(limit, 5) }).map((_, i) => (
          <div key={i} className="h-12 bg-[#151a2e] rounded-md animate-pulse border border-[#1c2333]" />
        ))}
      </div>
    );
  }

  if (deployments.length === 0) {
    return <p className="text-[12px] text-[#3d4454] py-4">No deployments recorded</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-separate border-spacing-y-1">
        <thead>
          <tr>
            <th className="pb-2 px-3">Deploy ID</th>
            <th className="pb-2 px-3">Service</th>
            <th className="pb-2 px-3">Risk Assessment</th>
            <th className="pb-2 px-3">Policy Engine</th>
            <th className="pb-2 px-3">Status</th>
            <th className="pb-2 px-3 text-right">Timestamp</th>
          </tr>
        </thead>
        <tbody>
          <AnimatePresence initial={false}>
            {deployments.slice(0, limit).map((dep, i) => {
              const dStyle = decisionStyle[dep.decision] || { bg: "bg-[#151a2e]", text: "text-[#4a5468]", border: "border-[#1c2333]", icon: Activity };
              const Icon = dStyle.icon;

              return (
                <motion.tr 
                  key={dep.id} 
                  initial={{ opacity: 0, y: -10, backgroundColor: "#1e293b" }}
                  animate={{ opacity: 1, y: 0, backgroundColor: "transparent" }}
                  transition={{ duration: 0.3 }}
                  className="group relative"
                >
                  <td className="py-2.5 px-3 bg-[#0f1422] group-hover:bg-[#151a2e] rounded-l-md border-y border-l border-[#1c2333] transition-colors">
                    <div className="flex items-center gap-2">
                      <GitCommit size={14} className="text-[#4a5468]" />
                      <span className="text-[#8892a8] mono text-[12px]">#{dep.id}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-3 bg-[#0f1422] group-hover:bg-[#151a2e] border-y border-[#1c2333] transition-colors">
                    <span className="text-[#c8cdd8] font-medium text-[13px]">{dep.repo_name?.split("/").pop() || "unknown"}</span>
                  </td>
                  <td className="py-2.5 px-3 bg-[#0f1422] group-hover:bg-[#151a2e] border-y border-[#1c2333] transition-colors">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full shrink-0 shadow-[0_0_8px_rgba(255,255,255,0.2)]" style={{
                        backgroundColor: dep.risk_score > 70 ? "#ef4444" : dep.risk_score > 40 ? "#eab308" : "#22c55e",
                        boxShadow: `0 0 8px ${dep.risk_score > 70 ? "rgba(239,68,68,0.4)" : dep.risk_score > 40 ? "rgba(234,179,8,0.4)" : "rgba(34,197,94,0.4)"}`
                      }} />
                      <span className="mono text-[#e2e8f0] text-[12px]">{dep.risk_score?.toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-3 bg-[#0f1422] group-hover:bg-[#151a2e] border-y border-[#1c2333] transition-colors">
                    <div className={`inline-flex items-center gap-1.5 text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${dStyle.bg} ${dStyle.text} ${dStyle.border}`}>
                      <Icon size={10} strokeWidth={2.5} />
                      {dep.decision || "—"}
                    </div>
                  </td>
                  <td className="py-2.5 px-3 bg-[#0f1422] group-hover:bg-[#151a2e] border-y border-[#1c2333] transition-colors">
                    <span className={`text-[12px] capitalize font-medium ${outcomeStyle[dep.outcome] || "text-[#4a5468]"}`}>
                      {dep.outcome || "pending"}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 bg-[#0f1422] group-hover:bg-[#151a2e] rounded-r-md border-y border-r border-[#1c2333] text-right transition-colors">
                    <span className="text-[11px] text-[#6b7280] mono">
                      {dep.timestamp ? new Date(dep.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : "—"}
                    </span>
                  </td>
                </motion.tr>
              );
            })}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  );
}
