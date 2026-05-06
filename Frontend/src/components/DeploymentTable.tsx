"use client";

import React, { useEffect, useState } from "react";
import { fetchAPI } from "@/lib/api";

interface Deployment {
  id: number;
  repo_name: string;
  environment: string;
  risk_score: number;
  decision: string;
  outcome: string;
  timestamp: string;
}

const decisionStyle: Record<string, string> = {
  ALLOW: "bg-emerald-500/8 text-emerald-400",
  WARN: "bg-amber-500/8 text-amber-400",
  BLOCK: "bg-rose-500/8 text-rose-400",
};

const outcomeStyle: Record<string, string> = {
  success: "text-emerald-400",
  failure: "text-rose-400",
  pending: "text-[#4a5468]",
};

export default function DeploymentTable({ limit = 10 }: { limit?: number }) {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<Deployment[]>(`/api/deployments/?limit=${limit}`)
      .then(setDeployments)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [limit]);

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: Math.min(limit, 5) }).map((_, i) => (
          <div key={i} className="h-10 bg-[#151a2e] rounded-md animate-pulse" />
        ))}
      </div>
    );
  }

  if (deployments.length === 0) {
    return <p className="text-[12px] text-[#3d4454] py-4">No deployments recorded</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-[#1c2333]">
            <th className="pb-2.5 pr-4">ID</th>
            <th className="pb-2.5 pr-4">Service</th>
            <th className="pb-2.5 pr-4">Risk</th>
            <th className="pb-2.5 pr-4">Decision</th>
            <th className="pb-2.5 pr-4">Outcome</th>
            <th className="pb-2.5 text-right">Time</th>
          </tr>
        </thead>
        <tbody>
          {deployments.slice(0, limit).map(dep => (
            <tr key={dep.id} className="border-b border-[#1c2333]/50 hover:bg-white/[0.01] transition-colors">
              <td className="py-2.5 pr-4 text-[#8892a8] mono">#{dep.id}</td>
              <td className="py-2.5 pr-4 text-[#c8cdd8] font-medium">{dep.repo_name?.split("/").pop() || "unknown"}</td>
              <td className="py-2.5 pr-4">
                <div className="flex items-center gap-1.5">
                  <div className="w-1 h-1 rounded-full shrink-0" style={{
                    backgroundColor: dep.risk_score > 70 ? "#ef4444" : dep.risk_score > 40 ? "#eab308" : "#22c55e"
                  }} />
                  <span className="mono text-[#c8cdd8]">{dep.risk_score?.toFixed(0)}%</span>
                </div>
              </td>
              <td className="py-2.5 pr-4">
                <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${decisionStyle[dep.decision] || "bg-[#151a2e] text-[#4a5468]"}`}>
                  {dep.decision || "—"}
                </span>
              </td>
              <td className="py-2.5 pr-4">
                <span className={`text-[12px] capitalize ${outcomeStyle[dep.outcome] || "text-[#4a5468]"}`}>
                  {dep.outcome || "pending"}
                </span>
              </td>
              <td className="py-2.5 text-right text-[#4a5468]">
                {dep.timestamp ? new Date(dep.timestamp).toLocaleDateString() : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
