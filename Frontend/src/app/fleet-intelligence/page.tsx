"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { fetchAPI } from "@/lib/api";
import RiskHeatmap from "@/components/RiskHeatmap";

interface FleetOverview {
  total_deployments: number; total_services: number;
  avg_risk_score: number; deployments_7d: number;
  blocked_total: number; block_rate: number;
}

interface ServiceProfile {
  service: string; total_deployments: number; avg_risk: number;
  max_risk: number; failure_rate: number; stability_score: number;
  risk_trend: string; health_status: string;
}

const healthBadge: Record<string, string> = {
  healthy: "text-emerald-400 bg-emerald-500/8",
  warning: "text-amber-400 bg-amber-500/8",
  critical: "text-rose-400 bg-rose-500/8",
  unknown: "text-[#4a5468] bg-[#151a2e]",
};

const trendIcon: Record<string, React.ReactNode> = {
  improving: <TrendingDown size={12} className="text-emerald-400" />,
  degrading: <TrendingUp size={12} className="text-rose-400" />,
  stable: <Minus size={12} className="text-[#4a5468]" />,
};

export default function FleetIntelligencePage() {
  const [overview, setOverview] = useState<FleetOverview | null>(null);
  const [services, setServices] = useState<ServiceProfile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchAPI<FleetOverview>("/api/fleet/overview"),
      fetchAPI<ServiceProfile[]>("/api/fleet/services"),
    ]).then(([ov, svcs]) => { setOverview(ov); setServices(svcs); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-5 w-40 bg-[#151a2e] rounded animate-pulse" />
        <div className="grid grid-cols-4 gap-3">{[1,2,3,4].map(i => <div key={i} className="h-20 bg-[#0f1422] border border-[#1c2333] rounded-lg animate-pulse" />)}</div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">Fleet Intelligence</h1>
        <p className="text-muted mt-0.5">Service risk profiles and fleet-wide deployment intelligence</p>
      </div>

      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Services", value: overview.total_services },
            { label: "Total Deploys", value: overview.total_deployments },
            { label: "Avg Risk", value: `${overview.avg_risk_score}%`, color: overview.avg_risk_score > 50 ? "text-rose-400" : "text-emerald-400" },
            { label: "Block Rate", value: `${overview.block_rate}%` },
          ].map((s, i) => (
            <motion.div key={s.label} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
              className="aegis-card">
              <div className="text-[10px] text-[#4a5468] uppercase tracking-wider">{s.label}</div>
              <div className={`text-xl font-semibold mono mt-1 ${s.color || "text-[#c8cdd8]"}`}>{s.value}</div>
            </motion.div>
          ))}
        </div>
      )}

      <RiskHeatmap />

      <div className="aegis-card">
        <h3 className="section-title mb-3">Service Profiles</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#1c2333]">
                {["Service", "Health", "Avg Risk", "Stability", "Failure Rate", "Deploys", "Trend"].map(h => (
                  <th key={h} className="text-left py-2.5 px-2 first:pl-0">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {services.map((s, i) => (
                <motion.tr key={s.service} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.025 }}
                  className="border-b border-[#1c2333]/50 hover:bg-white/[0.01] transition-colors">
                  <td className="py-2.5 px-2 first:pl-0 text-[13px] font-medium text-[#c8cdd8]">{s.service}</td>
                  <td className="py-2.5 px-2">
                    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${healthBadge[s.health_status] || healthBadge.unknown}`}>
                      {s.health_status}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 mono text-[13px]">{s.avg_risk.toFixed(1)}%</td>
                  <td className="py-2.5 px-2">
                    <div className="flex items-center gap-1.5">
                      <div className="w-14 h-1 bg-[#1c2333] rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${s.stability_score > 70 ? "bg-emerald-500" : s.stability_score > 40 ? "bg-amber-500" : "bg-rose-500"}`}
                          style={{ width: `${Math.max(0, s.stability_score)}%` }} />
                      </div>
                      <span className="text-[10px] text-[#4a5468] mono w-5">{s.stability_score.toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-2 mono text-[13px]">{(s.failure_rate * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-2 mono text-[13px]">{s.total_deployments}</td>
                  <td className="py-2.5 px-2">{trendIcon[s.risk_trend] || trendIcon.stable}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
