"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle, Clock, Zap, Target, Activity } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface Incident {
  incident_id: string; title: string; severity: string; status: string;
  deployment_ids: number[]; alert_ids: number[];
  created_at: string | null; resolved_at: string | null;
}

const severityColors: Record<string, string> = {
  CRITICAL: "text-rose-400 bg-rose-500/10 border-rose-500/20 shadow-[0_0_15px_rgba(244,63,94,0.1)]",
  HIGH: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  MEDIUM: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  LOW: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
};

const statusColors: Record<string, string> = {
  resolved: "text-emerald-400",
  active: "text-rose-400 font-bold",
  investigating: "text-amber-400",
};

export default function IncidentGraph() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<Incident[]>("/api/incidents/list?limit=15")
      .then(setIncidents)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="aegis-card"><div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-24 bg-[#151a2e] rounded-md animate-pulse border border-[#1c2333]" />)}</div></div>;
  }

  const activeIncidents = incidents.filter(i => i.status === "active");
  const otherIncidents = incidents.filter(i => i.status !== "active");

  return (
    <div className="space-y-4">
      {/* War Room Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 aegis-card bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-rose-900/10 via-[#0f1422] to-[#0f1422] relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Target size={120} className="text-rose-500" />
          </div>
          <h3 className="section-title text-rose-400 mb-2 flex items-center gap-2">
            <Activity size={14} className="animate-pulse" />
            Active Blast Radius
          </h3>
          <div className="flex items-end gap-4 mt-6">
            <div>
              <div className="text-[10px] text-[#8892a8] uppercase tracking-wide">Ongoing Incidents</div>
              <div className="text-3xl font-bold text-white mono">{activeIncidents.length}</div>
            </div>
            <div className="flex-1 pb-1">
              <div className="h-1.5 w-full bg-[#1c2333] rounded-full overflow-hidden">
                <motion.div 
                  className="h-full bg-rose-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, activeIncidents.length * 20)}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                />
              </div>
              <div className="text-[9px] text-[#4a5468] mt-1 text-right mono">CRITICAL IMPACT POTENTIAL</div>
            </div>
          </div>
        </div>
        <div className="aegis-card flex flex-col justify-center">
          <div className="text-[10px] text-[#8892a8] uppercase tracking-wide mb-1">Time to Resolution</div>
          <div className="text-2xl font-bold text-white mono mb-2">42<span className="text-sm text-[#4a5468] font-normal ml-1">min</span></div>
          <div className="text-[10px] text-emerald-400 flex items-center gap-1">
            ↓ 12% vs last month
          </div>
        </div>
      </div>

      <div className="aegis-card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title">Failure Chains</h3>
          <span className="text-[10px] text-[#4a5468] mono">{incidents.length} total</span>
        </div>

        {incidents.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-3">
              <CheckCircle size={24} className="text-emerald-500" />
            </div>
            <p className="text-[13px] font-medium text-[#c8cdd8]">Zero Active Incidents</p>
            <p className="text-[11px] text-[#4a5468] mt-1">Global infrastructure operating within safe limits</p>
          </div>
        ) : (
          <div className="space-y-3">
            {[...activeIncidents, ...otherIncidents].map((inc, i) => (
              <motion.div key={inc.incident_id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                className={`p-4 rounded-md border transition-all ${
                  inc.status === "active" 
                    ? "bg-[#151a2e] border-rose-500/30 hover:border-rose-500/50" 
                    : "bg-[#0a0e1a] border-[#1c2333] hover:border-[#232b3e]"
                }`}>
                
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${severityColors[inc.severity] || severityColors.LOW}`}>
                        {inc.severity}
                      </span>
                      {inc.status === "active" && (
                        <span className="flex items-center gap-1 text-[10px] text-rose-400 uppercase font-semibold bg-rose-500/10 px-1.5 py-0.5 rounded">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-live-dot" /> LIVE
                        </span>
                      )}
                    </div>
                    <span className={`text-[14px] font-medium ${inc.status === "active" ? "text-white" : "text-[#c8cdd8]"}`}>
                      {inc.title}
                    </span>
                  </div>
                  
                  <div className="text-right">
                    <span className={`text-[11px] font-medium uppercase tracking-wider ${statusColors[inc.status] || "text-[#4a5468]"}`}>
                      {inc.status}
                    </span>
                    <div className="text-[10px] text-[#4a5468] flex items-center gap-1 justify-end mt-1">
                      <Clock size={10} />
                      {inc.created_at ? new Date(inc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "—"}
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-[#1c2333] flex items-center gap-6">
                  <div className="flex items-center gap-1.5">
                    <Zap size={12} className="text-[#8892a8]" />
                    <span className="text-[11px] text-[#c8cdd8] mono">{inc.deployment_ids?.length || 0}</span>
                    <span className="text-[10px] text-[#4a5468]">Deploys Impacted</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Activity size={12} className="text-[#8892a8]" />
                    <span className="text-[11px] text-[#c8cdd8] mono">{inc.alert_ids?.length || 0}</span>
                    <span className="text-[10px] text-[#4a5468]">Correlated Alerts</span>
                  </div>
                  <div className="flex-1 text-right text-[10px] text-[#3d4454] mono">
                    ID: {inc.incident_id}
                  </div>
                </div>

              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
