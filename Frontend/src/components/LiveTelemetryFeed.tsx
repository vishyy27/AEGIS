"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, AlertTriangle, ShieldCheck, Zap, Radio } from "lucide-react";
import { useWebSocket, type WSMessage } from "@/lib/useWebSocket";

const typeConfig: Record<string, { icon: React.ReactNode; color: string }> = {
  deployment_event: { icon: <Zap size={13} />, color: "text-blue-400" },
  alert_event: { icon: <AlertTriangle size={13} />, color: "text-amber-400" },
  policy_decision: { icon: <ShieldCheck size={13} />, color: "text-emerald-400" },
  anomaly_event: { icon: <Activity size={13} />, color: "text-rose-400" },
};

function EventItem({ msg }: { msg: WSMessage }) {
  const type = (msg.type as string) || "unknown";
  const cfg = typeConfig[type] || { icon: <Radio size={13} />, color: "text-[#4b5563]" };
  const ts = msg.timestamp || msg._broadcast_at;

  let label = type.replace(/_/g, " ");
  if (type === "deployment_event") label = `Deploy #${msg.deployment_id || "—"}`;
  else if (type === "policy_decision") {
    const d = msg.decision as Record<string,unknown>;
    label = `Policy → ${d?.decision || "—"}`;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2.5 px-3 py-2 rounded-md hover:bg-white/[0.02] transition-colors"
    >
      <span className={cfg.color}>{cfg.icon}</span>
      <span className="text-[12px] text-[#c8cdd8] flex-1 truncate">{label}</span>
      <span className="text-[10px] text-[#3d4454] mono shrink-0">
        {ts ? new Date(ts as string).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : ""}
      </span>
    </motion.div>
  );
}

export default function LiveTelemetryFeed() {
  const { messages, connected } = useWebSocket(["telemetry", "alerts", "deployments", "policy"]);

  return (
    <div className="aegis-card h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="section-title">Live Feed</h3>
        <div className="flex items-center gap-1.5">
          <span className={`w-[5px] h-[5px] rounded-full ${connected ? "bg-emerald-400 animate-live-dot" : "bg-[#3d4454]"}`} />
          <span className="text-[10px] text-[#4a5468]">{connected ? "Live" : "Offline"}</span>
        </div>
      </div>

      <div className="space-y-0.5 max-h-[360px] overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Radio size={20} className="text-[#232b3e] mb-2" />
              <p className="text-[12px] text-[#3d4454]">Listening for events</p>
              <p className="text-[11px] text-[#2a3040] mt-0.5">Events will stream in real-time</p>
            </div>
          ) : (
            messages.slice(0, 25).map((msg, i) => (
              <EventItem key={`${msg.type}-${i}`} msg={msg} />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
