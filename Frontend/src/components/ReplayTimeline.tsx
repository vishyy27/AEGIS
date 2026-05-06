"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Play, Pause, SkipBack, SkipForward, Zap, AlertTriangle, Activity } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface TimelineItem {
  type: string; timestamp: string; relative_seconds: number;
  data: Record<string, unknown>;
}

interface ReplayData {
  deployment_id: number; service: string; risk_score: number;
  decision: string; outcome: string; timeline: TimelineItem[];
}

const typeConfig: Record<string, { icon: React.ReactNode; color: string }> = {
  event: { icon: <Zap size={11} />, color: "text-blue-400" },
  alert: { icon: <AlertTriangle size={11} />, color: "text-amber-400" },
  anomaly: { icon: <Activity size={11} />, color: "text-rose-400" },
};

export default function ReplayTimeline({ deploymentId }: { deploymentId: number }) {
  const [data, setData] = useState<ReplayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    fetchAPI<ReplayData>(`/api/replay/timeline/${deploymentId}`)
      .then(d => { setData(d); setIdx(0); setPlaying(false); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [deploymentId]);

  useEffect(() => {
    if (!playing || !data) return;
    const t = setInterval(() => {
      setIdx(prev => {
        if (prev >= data.timeline.length - 1) { setPlaying(false); return prev; }
        return prev + 1;
      });
    }, 600);
    return () => clearInterval(t);
  }, [playing, data]);

  if (loading) return <div className="aegis-card"><div className="h-48 bg-[#151a2e] rounded-md animate-pulse" /></div>;
  if (!data) return <div className="aegis-card"><p className="text-[12px] text-[#3d4454] text-center py-12">No replay data</p></div>;

  const progress = data.timeline.length > 0 ? ((idx + 1) / data.timeline.length) * 100 : 0;

  return (
    <div className="aegis-card flex flex-col h-full">
      {/* Meta */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="section-title">Timeline</h3>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-[#4a5468] mono">#{data.deployment_id}</span>
          <span className="text-[11px] text-[#6b7280]">{data.service}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 mb-3 bg-[#0a0e1a] rounded-md p-2 border border-[#1c2333]">
        <button onClick={() => setIdx(0)} className="p-1 hover:bg-white/[0.05] rounded transition-colors">
          <SkipBack size={13} className="text-[#6b7280]" />
        </button>
        <button onClick={() => setPlaying(!playing)} className="p-1.5 bg-blue-600 hover:bg-blue-500 rounded-md transition-colors">
          {playing ? <Pause size={13} className="text-white" /> : <Play size={13} className="text-white" />}
        </button>
        <button onClick={() => setIdx(Math.min(idx + 1, data.timeline.length - 1))} className="p-1 hover:bg-white/[0.05] rounded transition-colors">
          <SkipForward size={13} className="text-[#6b7280]" />
        </button>

        <div className="flex-1 h-1 bg-[#1c2333] rounded-full overflow-hidden mx-2">
          <motion.div className="h-full bg-blue-500 rounded-full" animate={{ width: `${progress}%` }} transition={{ duration: 0.15 }} />
        </div>
        <span className="text-[10px] text-[#4a5468] mono shrink-0">{idx + 1}/{data.timeline.length}</span>
      </div>

      {/* Events */}
      <div className="space-y-0.5 flex-1 overflow-y-auto">
        {data.timeline.map((item, i) => {
          const isActive = i === idx;
          const isPast = i < idx;
          const cfg = typeConfig[item.type] || typeConfig.event;
          const eventLabel = (item.data?.event_type as string) || (item.data?.alert_type as string) || item.type;

          return (
            <div key={i} onClick={() => setIdx(i)}
              className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md cursor-pointer transition-all text-[12px] ${
                isActive ? "bg-blue-500/8 border border-blue-500/15" :
                isPast ? "opacity-40" : "opacity-25 hover:opacity-40"
              }`}>
              <span className={cfg.color}>{cfg.icon}</span>
              <span className={`flex-1 truncate ${isActive ? "text-[#c8cdd8]" : "text-[#6b7280]"}`}>{eventLabel}</span>
              <span className="text-[9px] text-[#3d4454] mono shrink-0">+{item.relative_seconds?.toFixed(1)}s</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
