"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle, Clock } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface Incident {
  incident_id: string; title: string; severity: string; status: string;
  deployment_ids: number[]; alert_ids: number[];
  created_at: string | null; resolved_at: string | null;
}

const severityColors: Record<string, string> = {
  CRITICAL: "text-rose-400 bg-rose-500/8 border-rose-500/15",
  HIGH: "text-amber-400 bg-amber-500/8 border-amber-500/15",
  MEDIUM: "text-yellow-400 bg-yellow-500/8 border-yellow-500/15",
  LOW: "text-emerald-400 bg-emerald-500/8 border-emerald-500/15",
};

const statusColors: Record<string, string> = {
  resolved: "text-emerald-400",
  active: "text-rose-400",
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
    return <div className="aegis-card"><div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-16 bg-[#151a2e] rounded-md animate-pulse" />)}</div></div>;
  }

  return (
    <div className="aegis-card">
      <h3 className="section-title mb-4">Incidents</h3>

      {incidents.length === 0 ? (
        <div className="text-center py-12">
          <CheckCircle size={20} className="text-emerald-500/30 mx-auto mb-2" />
          <p className="text-[13px] text-[#4a5468]">No incidents detected</p>
          <p className="text-[11px] text-[#2a3040] mt-0.5">System operating normally</p>
        </div>
      ) : (
        <div className="space-y-2">
          {incidents.map((inc, i) => (
            <motion.div key={inc.incident_id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
              className="flex items-center justify-between px-3.5 py-3 rounded-md bg-[#0a0e1a] border border-[#1c2333] hover:border-[#232b3e] transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-medium text-[#c8cdd8] truncate">{inc.title}</span>
                  <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${severityColors[inc.severity] || severityColors.LOW}`}>
                    {inc.severity}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-[10px] text-[#3d4454] mono">{inc.incident_id}</span>
                  <span className="text-[10px] text-[#3d4454] flex items-center gap-1">
                    <Clock size={9} />
                    {inc.created_at ? new Date(inc.created_at).toLocaleDateString() : ""}
                  </span>
                  <span className="text-[10px] text-[#3d4454]">{inc.deployment_ids?.length || 0} deploys · {inc.alert_ids?.length || 0} alerts</span>
                </div>
              </div>
              <span className={`text-[10px] font-medium ${statusColors[inc.status] || "text-[#4a5468]"}`}>
                {inc.status}
              </span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
