"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Clock, Play, Pause, SkipBack, SkipForward, AlertTriangle, Zap, Activity } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface TimelineItem {
  type: string;
  timestamp: string;
  relative_seconds: number;
  data: Record<string, unknown>;
}

interface ReplayData {
  deployment_id: number;
  service: string;
  risk_score: number;
  decision: string;
  timeline: TimelineItem[];
  started_at: string;
}

const typeIcons: Record<string, React.ReactNode> = {
  event: <Zap size={12} className="text-cyan-400" />,
  alert: <AlertTriangle size={12} className="text-amber-400" />,
  anomaly: <Activity size={12} className="text-red-400" />,
};

export default function ReplayTimeline({ deploymentId }: { deploymentId: number }) {
  const [data, setData] = useState<ReplayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    fetchAPI<ReplayData>(`/api/replay/timeline/${deploymentId}`)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [deploymentId]);

  useEffect(() => {
    if (!playing || !data) return;
    const interval = setInterval(() => {
      setCurrentIndex(prev => {
        if (prev >= data.timeline.length - 1) {
          setPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 800);
    return () => clearInterval(interval);
  }, [playing, data]);

  if (loading) return <div className="aegis-card animate-pulse"><div className="h-64 bg-slate-800/50 rounded-lg" /></div>;
  if (!data) return <div className="aegis-card"><p className="text-sm text-slate-500 text-center py-10">No replay data available</p></div>;

  const progress = data.timeline.length > 0 ? ((currentIndex + 1) / data.timeline.length) * 100 : 0;

  return (
    <div className="aegis-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Clock size={18} className="text-violet-400" />
          <h3 className="section-title">Deployment Replay</h3>
        </div>
        <span className="text-xs text-slate-500 mono">#{data.deployment_id} · {data.service}</span>
      </div>

      {/* Playback controls */}
      <div className="flex items-center gap-3 mb-4 bg-slate-900/50 rounded-lg p-3">
        <button onClick={() => setCurrentIndex(0)} className="p-1.5 hover:bg-slate-700 rounded transition-colors">
          <SkipBack size={14} className="text-slate-400" />
        </button>
        <button onClick={() => setPlaying(!playing)} className="p-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg transition-colors">
          {playing ? <Pause size={16} className="text-white" /> : <Play size={16} className="text-white" />}
        </button>
        <button onClick={() => setCurrentIndex(Math.min(currentIndex + 1, data.timeline.length - 1))} className="p-1.5 hover:bg-slate-700 rounded transition-colors">
          <SkipForward size={14} className="text-slate-400" />
        </button>

        {/* Progress bar */}
        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <motion.div className="h-full bg-gradient-to-r from-cyan-500 to-violet-500 rounded-full" animate={{ width: `${progress}%` }} />
        </div>
        <span className="text-[10px] text-slate-500 mono">{currentIndex + 1}/{data.timeline.length}</span>
      </div>

      {/* Timeline events */}
      <div className="space-y-1 max-h-[300px] overflow-y-auto pr-1">
        {data.timeline.map((item, i) => {
          const isActive = i === currentIndex;
          const isPast = i < currentIndex;
          return (
            <motion.div
              key={i}
              onClick={() => setCurrentIndex(i)}
              className={`flex items-start gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all ${
                isActive ? "bg-cyan-500/10 border border-cyan-500/20" :
                isPast ? "opacity-50" : "opacity-30 hover:opacity-60"
              }`}
              animate={{ opacity: isActive ? 1 : isPast ? 0.5 : 0.3 }}
            >
              <div className="mt-0.5">{typeIcons[item.type] || <Zap size={12} className="text-slate-500" />}</div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-medium text-slate-300 truncate">
                    {(item.data?.event_type as string) || (item.data?.alert_type as string) || (item.data?.anomaly_type as string) || item.type}
                  </span>
                  <span className="text-[10px] text-slate-600 mono shrink-0 ml-2">+{item.relative_seconds?.toFixed(1)}s</span>
                </div>
                <p className="text-[10px] text-slate-500 truncate">
                  {(item.data?.message as string) || (item.data?.description as string) || ""}
                </p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
