"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Network, TrendingUp, TrendingDown, Minus, ArrowUpRight } from "lucide-react";
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
  risk_trend: string; health_status: string; last_deployment: string | null;
}

const healthColors: Record<string, string> = {
  healthy: "text-emerald-400 bg-emerald-500/10",
  warning: "text-amber-400 bg-amber-500/10",
  critical: "text-red-400 bg-red-500/10",
  unknown: "text-slate-400 bg-slate-500/10",
};

const trendIcons: Record<string, React.ReactNode> = {
  improving: <TrendingDown size={14} className="text-emerald-400" />,
  degrading: <TrendingUp size={14} className="text-red-400" />,
  stable: <Minus size={14} className="text-slate-400" />,
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

  if (loading) return <div className="flex items-center justify-center h-[60vh] text-slate-500">Loading fleet intelligence...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title text-gradient-cyan flex items-center gap-3">
          <Network size={28} className="text-cyan-400" />
          Fleet Intelligence
        </h1>
        <p className="text-muted mt-1">Multi-service risk profiles and fleet-wide deployment intelligence</p>
      </div>

      {/* Overview stats */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Services", value: overview.total_services, color: "text-cyan-400" },
            { label: "Total Deployments", value: overview.total_deployments, color: "text-blue-400" },
            { label: "Avg Risk Score", value: `${overview.avg_risk_score}%`, color: overview.avg_risk_score > 50 ? "text-red-400" : "text-emerald-400" },
            { label: "Block Rate", value: `${overview.block_rate}%`, color: "text-amber-400" },
          ].map((stat, i) => (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
              className="aegis-card text-center">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider">{stat.label}</div>
              <div className={`text-2xl font-bold mono mt-1 ${stat.color}`}>{stat.value}</div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Heatmap */}
      <RiskHeatmap />

      {/* Service Profiles */}
      <div className="aegis-card">
        <h3 className="section-title mb-4">Service Risk Profiles</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 text-xs uppercase tracking-wider">
                <th className="text-left py-3 pr-4">Service</th>
                <th className="text-center py-3 px-2">Health</th>
                <th className="text-center py-3 px-2">Avg Risk</th>
                <th className="text-center py-3 px-2">Stability</th>
                <th className="text-center py-3 px-2">Failure Rate</th>
                <th className="text-center py-3 px-2">Deploys</th>
                <th className="text-center py-3 px-2">Trend</th>
              </tr>
            </thead>
            <tbody>
              {services.map((s, i) => (
                <motion.tr key={s.service} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
                  className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                  <td className="py-3 pr-4 font-medium text-slate-200">{s.service}</td>
                  <td className="text-center py-3 px-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${healthColors[s.health_status] || healthColors.unknown}`}>
                      {s.health_status}
                    </span>
                  </td>
                  <td className="text-center py-3 px-2 mono text-slate-300">{s.avg_risk.toFixed(1)}%</td>
                  <td className="text-center py-3 px-2">
                    <div className="flex items-center justify-center gap-1">
                      <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${s.stability_score > 70 ? "bg-emerald-500" : s.stability_score > 40 ? "bg-amber-500" : "bg-red-500"}`}
                          style={{ width: `${Math.max(0, s.stability_score)}%` }} />
                      </div>
                      <span className="text-[10px] text-slate-500 mono">{s.stability_score.toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="text-center py-3 px-2 mono text-slate-300">{(s.failure_rate * 100).toFixed(1)}%</td>
                  <td className="text-center py-3 px-2 mono text-slate-300">{s.total_deployments}</td>
                  <td className="text-center py-3 px-2">{trendIcons[s.risk_trend] || trendIcons.stable}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
