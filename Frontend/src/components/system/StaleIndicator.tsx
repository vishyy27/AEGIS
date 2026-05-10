"use client";

import React from "react";
import { Clock } from "lucide-react";
import { useTelemetryStore } from "@/store/telemetryStore";

export default function StaleIndicator({ thresholdMs = 30000 }: { thresholdMs?: number }) {
  const lastUpdated = useTelemetryStore(state => state.lastUpdated);
  const [stale, setStale] = React.useState(false);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setStale(Date.now() - lastUpdated > thresholdMs);
    }, 5000);
    return () => clearInterval(interval);
  }, [lastUpdated, thresholdMs]);

  if (!stale) return null;

  return (
    <div className="flex items-center gap-1.5 text-[10px] text-amber-400/80 bg-amber-500/5 border border-amber-500/10 px-2 py-1 rounded">
      <Clock size={10} />
      <span>Data may be stale</span>
    </div>
  );
}
