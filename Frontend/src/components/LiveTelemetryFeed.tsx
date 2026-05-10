"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, AlertTriangle, ShieldCheck, Zap, Radio, Loader2 } from "lucide-react";
import { type WSMessage } from "@/providers/WebSocketProvider";

const typeConfig: Record<string, { icon: React.ReactNode; color: string; bg: string }> = {
  deployment_event: { icon: <Zap size={13} />, color: "text-blue-400", bg: "bg-blue-500/10" },
  alert_event: { icon: <AlertTriangle size={13} />, color: "text-amber-400", bg: "bg-amber-500/10" },
  policy_decision: { icon: <ShieldCheck size={13} />, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  anomaly_event: { icon: <Activity size={13} />, color: "text-rose-400", bg: "bg-rose-500/10" },
};

function EventItem({ msg }: { msg: WSMessage }) {
  const type = (msg.type as string) || "unknown";
  const cfg = typeConfig[type] || { icon: <Radio size={13} />, color: "text-[#8892a8]", bg: "bg-[#151a2e]" };
  const ts = msg.timestamp || msg._broadcast_at;

  let label = type.replace(/_/g, " ");
  let meta = "";
  
  if (type === "deployment_event") {
    label = `Deploy #${msg.deployment_id || "—"}`;
    meta = (msg.event_type as string) || "";
  } else if (type === "policy_decision") {
    const d = msg.decision as Record<string,unknown>;
    label = `Policy: ${d?.decision || "—"}`;
    meta = d?.reason ? String(d.reason) : "";
  } else if (type === "anomaly_event") {
    label = "Anomaly Detected";
    meta = (msg.anomaly_type as string) || "";
  } else if (type === "alert_event") {
    label = "Alert Triggered";
    meta = (msg.alert_type as string) || "";
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className="group flex flex-col gap-1.5 px-3 py-2.5 rounded-md hover:bg-white/[0.02] border border-transparent hover:border-[#1c2333] transition-all cursor-default"
    >
      <div className="flex items-center gap-2.5">
        <div className={`p-1.5 rounded-md ${cfg.bg} ${cfg.color}`}>
          {cfg.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-baseline">
            <span className="text-[12px] font-medium text-[#e2e8f0] truncate capitalize">{label}</span>
            <span className="text-[10px] text-[#4a5468] mono shrink-0 ml-2">
              {ts ? new Date(ts as string).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : ""}
            </span>
          </div>
          {meta && <div className="text-[11px] text-[#8892a8] truncate mt-0.5">{meta}</div>}
        </div>
      </div>
    </motion.div>
  );
}

import { useTelemetryStore } from "@/store/telemetryStore";

export default function LiveTelemetryFeed() {
  const messages = useTelemetryStore(state => state.recentMessages);
  const connectionStatus = useTelemetryStore(state => state.connectionStatus);
  const connected = connectionStatus === 'connected';
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => setMounted(true), []);

  return (
    <div className="aegis-card h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="section-title">Live Telemetry</h3>
          {messages.length > 0 && <span className="text-[10px] bg-[#151a2e] text-[#8892a8] px-1.5 py-0.5 rounded mono">{messages.length}</span>}
        </div>
        {mounted && (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#0f1422] border border-[#1c2333]">
            <span className={`w-[6px] h-[6px] rounded-full ${connected ? "bg-emerald-500 animate-live-dot" : "bg-rose-500"}`} />
            <span className="text-[9px] text-[#8892a8] uppercase tracking-wide font-medium">{connected ? "Connected" : "Reconnecting..."}</span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-1 relative pr-1 -mr-1">
        {!mounted ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Loader2 size={18} className="text-[#3d4454] animate-spin mb-3" />
            <p className="text-[12px] text-[#4a5468]">Initializing feed...</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {messages.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center py-16 text-center absolute inset-0"
              >
                <div className="w-12 h-12 rounded-full bg-[#151a2e] flex items-center justify-center mb-3">
                  <Radio size={20} className="text-[#4a5468]" />
                </div>
                <p className="text-[13px] font-medium text-[#c8cdd8]">Awaiting telemetry</p>
                <p className="text-[11px] text-[#4a5468] mt-1 max-w-[200px]">Live events from the cluster will appear here automatically</p>
              </motion.div>
            ) : (
              messages.slice(0, 50).map((msg, i) => (
                <EventItem key={`${msg.type}-${i}-${msg.timestamp || Math.random()}`} msg={msg} />
              ))
            )}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
