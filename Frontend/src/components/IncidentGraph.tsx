"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertOctagon, Clock, CheckCircle, AlertTriangle } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface Incident {
  incident_id: string;
  title: string;
  severity: string;
  status: string;
  deployment_ids: number[];
  alert_ids: number[];
  created_at: string | null;
  resolved_at: string | null;
}

const severityConfig: Record<string, { color: string; bg: string; icon: React.ReactNode }> = {
  CRITICAL: { color: "text-red-400", bg: "bg-red-500/10 border-red-500/20", icon: <AlertOctagon size={16} /> },
  HIGH: { color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/20", icon: <AlertTriangle size={16} /> },
  MEDIUM: { color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20", icon: <AlertTriangle size={16} /> },
  LOW: { color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", icon: <CheckCircle size={16} /> },
};

export default function IncidentGraph() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<Incident[]>("/api/incidents/list?limit=10")
      .then(setIncidents)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="aegis-card animate-pulse"><div className="h-64 bg-slate-800/50 rounded-lg" /></div>;
  }

  return (
    <div className="aegis-card">
      <div className="flex items-center gap-2 mb-6">
        <AlertOctagon size={18} className="text-red-400" />
        <h3 className="section-title">Incident Timeline</h3>
      </div>

      {incidents.length === 0 ? (
        <div className="text-center py-10">
          <CheckCircle size={32} className="text-emerald-500/30 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No incidents detected</p>
          <p className="text-xs text-slate-600 mt-1">System operating normally</p>
        </div>
      ) : (
        <div className="space-y-3">
          {incidents.map((inc, i) => {
            const cfg = severityConfig[inc.severity] || severityConfig.LOW;
            return (
              <motion.div
                key={inc.incident_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`${cfg.bg} border rounded-lg px-4 py-3`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 ${cfg.color}`}>{cfg.icon}</div>
                    <div>
                      <h4 className="text-sm font-medium text-slate-200">{inc.title}</h4>
                      <div className="flex items-center gap-3 mt-1">
                        <span className={`text-[10px] font-bold ${cfg.color}`}>{inc.severity}</span>
                        <span className="text-[10px] text-slate-500 mono">{inc.incident_id}</span>
                        <span className="text-[10px] text-slate-600 flex items-center gap-1">
                          <Clock size={10} />
                          {inc.created_at ? new Date(inc.created_at).toLocaleString() : ""}
                        </span>
                      </div>
                    </div>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                    inc.status === "resolved" ? "bg-emerald-500/10 text-emerald-400" :
                    inc.status === "active" ? "bg-red-500/10 text-red-400" :
                    "bg-amber-500/10 text-amber-400"
                  }`}>
                    {inc.status}
                  </span>
                </div>
                <div className="flex gap-4 mt-2 ml-7">
                  <span className="text-[10px] text-slate-500">{inc.deployment_ids?.length || 0} deployments</span>
                  <span className="text-[10px] text-slate-500">{inc.alert_ids?.length || 0} alerts</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
