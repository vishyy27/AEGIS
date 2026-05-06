"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, AlertTriangle, ShieldCheck, Zap, Radio } from "lucide-react";
import { useWebSocket, type WSMessage } from "@/lib/useWebSocket";

const eventIcons: Record<string, React.ReactNode> = {
  deployment_event: <Zap size={14} className="text-cyan-400" />,
  alert_event: <AlertTriangle size={14} className="text-amber-400" />,
  policy_decision: <ShieldCheck size={14} className="text-emerald-400" />,
  anomaly_event: <Activity size={14} className="text-red-400" />,
  system_status: <Radio size={14} className="text-violet-400" />,
};

const severityColors: Record<string, string> = {
  INFO: "border-l-cyan-500",
  WARNING: "border-l-amber-500",
  ERROR: "border-l-red-500",
  CRITICAL: "border-l-red-600",
};

function EventCard({ msg, index }: { msg: WSMessage; index: number }) {
  const type = (msg.type as string) || "unknown";
  const icon = eventIcons[type] || <Activity size={14} className="text-slate-400" />;
  const severity = (msg.severity as string) || (msg.event_data as Record<string,unknown>)?.severity as string || "INFO";
  const borderColor = severityColors[severity] || "border-l-slate-600";
  const ts = msg.timestamp || msg._broadcast_at;

  let title = type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  let subtitle = "";

  if (type === "deployment_event") {
    title = `Deployment #${msg.deployment_id || "?"}`;
    subtitle = (msg.event_type as string) || "";
  } else if (type === "alert_event") {
    const alert = msg.alert as Record<string,unknown>;
    title = `Alert: ${alert?.alert_type || "Unknown"}`;
    subtitle = (alert?.severity as string) || "";
  } else if (type === "policy_decision") {
    const decision = msg.decision as Record<string,unknown>;
    title = `Policy → ${decision?.decision || "?"}`;
    subtitle = `Risk: ${decision?.risk_score || "?"}`;
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20, height: 0 }}
      animate={{ opacity: 1, x: 0, height: "auto" }}
      exit={{ opacity: 0, x: 20, height: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`border-l-2 ${borderColor} bg-slate-900/50 rounded-r-lg px-4 py-3 flex items-start gap-3`}
    >
      <div className="mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-200 truncate">{title}</span>
          <span className="text-[10px] text-slate-600 mono shrink-0 ml-2">
            {ts ? new Date(ts as string).toLocaleTimeString() : ""}
          </span>
        </div>
        {subtitle && <span className="text-xs text-slate-500">{subtitle}</span>}
      </div>
    </motion.div>
  );
}

export default function LiveTelemetryFeed() {
  const { messages, connected } = useWebSocket(["telemetry", "alerts", "deployments", "policy"]);

  return (
    <div className="aegis-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-cyan-400" />
          <h3 className="section-title">Live Telemetry</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-500 animate-live-dot" : "bg-red-500"}`} />
          <span className="text-xs text-slate-500">{connected ? "Connected" : "Disconnected"}</span>
        </div>
      </div>

      <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
        <AnimatePresence mode="popLayout">
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-12 text-slate-600"
            >
              <Radio size={32} className="mb-3 animate-pulse-glow" />
              <p className="text-sm">Waiting for telemetry events...</p>
              <p className="text-xs mt-1">Events will appear in real-time</p>
            </motion.div>
          ) : (
            messages.slice(0, 20).map((msg, i) => (
              <EventCard key={`${msg.type}-${msg.timestamp || i}-${i}`} msg={msg} index={i} />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
