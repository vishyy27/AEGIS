"use client";

import React from "react";
import { WifiOff, RefreshCw } from "lucide-react";
import { useTelemetryStore } from "@/store/telemetryStore";

export default function ConnectionOverlay() {
  const connectionStatus = useTelemetryStore(state => state.connectionStatus);

  if (connectionStatus === "connected") return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 animate-in fade-in slide-in-from-bottom-2">
      <div className={`flex items-center gap-2.5 px-4 py-2.5 rounded-lg border shadow-xl backdrop-blur-md ${
        connectionStatus === "reconnecting"
          ? "bg-amber-950/80 border-amber-500/30 text-amber-200"
          : "bg-rose-950/80 border-rose-500/30 text-rose-200"
      }`}>
        {connectionStatus === "reconnecting" ? (
          <RefreshCw size={14} className="animate-spin" />
        ) : (
          <WifiOff size={14} />
        )}
        <span className="text-[12px] font-medium">
          {connectionStatus === "reconnecting" ? "Reconnecting to telemetry..." : "Telemetry disconnected"}
        </span>
        <span className={`w-2 h-2 rounded-full ${
          connectionStatus === "reconnecting" ? "bg-amber-400 animate-pulse" : "bg-rose-400"
        }`} />
      </div>
    </div>
  );
}
