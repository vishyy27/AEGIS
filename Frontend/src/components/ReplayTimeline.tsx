"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Pause, SkipBack, SkipForward, Zap, AlertTriangle, Activity, CheckCircle, Target } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface TimelineItem {
  type: string; timestamp: string; relative_seconds: number;
  data: Record<string, unknown>;
}

interface ReplayData {
  deployment_id: number; service: string; risk_score: number;
  decision: string; outcome: string; timeline: TimelineItem[];
}

const typeConfig: Record<string, { icon: React.ReactNode; color: string; bg: string }> = {
  event: { icon: <Zap size={14} />, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  alert: { icon: <AlertTriangle size={14} />, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.15)]" },
  anomaly: { icon: <Activity size={14} />, color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20 shadow-[0_0_15px_rgba(244,63,94,0.15)]" },
  success: { icon: <CheckCircle size={14} />, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" }
};

export default function ReplayTimeline({ deploymentId }: { deploymentId: number }) {
  const [data, setData] = useState<ReplayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(600);

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
    }, playbackSpeed);
    return () => clearInterval(t);
  }, [playing, data, playbackSpeed]);

  if (loading) return <div className="aegis-card h-full flex items-center justify-center"><div className="h-4 w-4 bg-blue-500 rounded-full animate-ping" /></div>;
  if (!data) return <div className="aegis-card h-full flex flex-col items-center justify-center"><p className="text-[12px] text-[#3d4454]">No replay data available</p></div>;

  const progress = data.timeline.length > 0 ? ((idx + 1) / data.timeline.length) * 100 : 0;
  
  // Cinematic state derivation based on current idx
  const pastEvents = data.timeline.slice(0, idx + 1);
  const activeAlerts = pastEvents.filter(e => e.type === "alert").length;
  const activeAnomalies = pastEvents.filter(e => e.type === "anomaly").length;
  
  const currentRisk = Math.min(100, Math.max(0, data.risk_score + (activeAnomalies * 15) + (activeAlerts * 5)));
  const systemState = activeAnomalies > 1 ? "CRITICAL" : activeAlerts > 0 ? "DEGRADED" : "NOMINAL";
  
  return (
    <div className="aegis-card flex flex-col h-full relative overflow-hidden">
      {/* Background Cinematic FX */}
      <div className={`absolute top-0 right-0 w-64 h-64 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] opacity-10 blur-3xl rounded-full transition-colors duration-1000 ${
        systemState === 'CRITICAL' ? 'from-rose-500 to-transparent' : systemState === 'DEGRADED' ? 'from-amber-500 to-transparent' : 'from-emerald-500 to-transparent'
      }`} />
      
      {/* Meta */}
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div>
          <h3 className="section-title text-white flex items-center gap-2">
            <Target size={14} className="text-blue-400" />
            Cinematic Replay Engine
          </h3>
          <p className="text-[11px] text-[#8892a8] mt-0.5">Chronological reconstruction</p>
        </div>
        <div className="flex items-center gap-2 bg-[#0f1422] border border-[#1c2333] px-2.5 py-1 rounded-md">
          <span className="text-[10px] text-[#4a5468] uppercase tracking-wider">Deploy</span>
          <span className="text-[11px] text-[#e2e8f0] mono font-medium">#{data.deployment_id}</span>
        </div>
      </div>

      {/* Cinematic HUD */}
      <div className="grid grid-cols-3 gap-3 mb-4 relative z-10">
        <div className="bg-[#0f1422] border border-[#1c2333] rounded-md p-3">
          <div className="text-[9px] text-[#4a5468] uppercase tracking-wider mb-1">Simulated Risk</div>
          <div className={`text-2xl font-bold mono transition-colors duration-500 ${
            currentRisk > 75 ? 'text-rose-400' : currentRisk > 40 ? 'text-amber-400' : 'text-emerald-400'
          }`}>
            {currentRisk.toFixed(0)}%
          </div>
        </div>
        <div className="bg-[#0f1422] border border-[#1c2333] rounded-md p-3">
          <div className="text-[9px] text-[#4a5468] uppercase tracking-wider mb-1">System State</div>
          <div className={`text-sm font-bold uppercase mt-1.5 transition-colors duration-500 ${
            systemState === 'CRITICAL' ? 'text-rose-400' : systemState === 'DEGRADED' ? 'text-amber-400' : 'text-emerald-400'
          }`}>
            {systemState}
          </div>
        </div>
        <div className="bg-[#0f1422] border border-[#1c2333] rounded-md p-3 flex flex-col justify-between">
          <div className="text-[9px] text-[#4a5468] uppercase tracking-wider">Active Anomalies</div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-[#c8cdd8] mono">{activeAnomalies}</span>
            {activeAnomalies > 0 && (
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 mb-4 bg-[#0a0e1a] rounded-md p-2 border border-[#1c2333] relative z-10 shadow-[inset_0_1px_4px_rgba(0,0,0,0.5)]">
        <button onClick={() => setIdx(0)} className="p-1 hover:bg-[#151a2e] rounded transition-colors">
          <SkipBack size={14} className="text-[#6b7280]" />
        </button>
        <button onClick={() => setPlaying(!playing)} className="p-1.5 bg-blue-600 hover:bg-blue-500 rounded-md transition-colors shadow-[0_0_10px_rgba(37,99,235,0.3)]">
          {playing ? <Pause size={14} className="text-white" /> : <Play size={14} className="text-white fill-white ml-0.5" />}
        </button>
        <button onClick={() => setIdx(Math.min(idx + 1, data.timeline.length - 1))} className="p-1 hover:bg-[#151a2e] rounded transition-colors">
          <SkipForward size={14} className="text-[#6b7280]" />
        </button>

        <div className="flex-1 h-1.5 bg-[#1c2333] rounded-full overflow-hidden mx-3 shadow-[inset_0_1px_2px_rgba(0,0,0,0.5)]">
          <motion.div className="h-full bg-blue-500 rounded-full" animate={{ width: `${progress}%` }} transition={{ duration: 0.15 }} />
        </div>
        
        <div className="flex items-center gap-2 px-2">
          <span className="text-[9px] text-[#4a5468] uppercase tracking-wider">Speed</span>
          <select 
            value={playbackSpeed} 
            onChange={e => setPlaybackSpeed(Number(e.target.value))}
            className="bg-transparent text-[10px] text-[#c8cdd8] mono outline-none cursor-pointer"
          >
            <option value={1000}>1x</option>
            <option value={600}>1.5x</option>
            <option value={300}>2x</option>
          </select>
        </div>
        <span className="text-[10px] text-[#4a5468] mono shrink-0">{idx + 1}/{data.timeline.length}</span>
      </div>

      {/* Events */}
      <div className="space-y-2 flex-1 overflow-y-auto pr-2 relative z-10 scrollbar-hide">
        <AnimatePresence initial={false}>
          {pastEvents.map((item, i) => {
            const isLatest = i === idx;
            const cfg = typeConfig[item.type] || typeConfig.event;
            const eventLabel = (item.data?.event_type as string) || (item.data?.alert_type as string) || item.type;

            return (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, x: -20, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                onClick={() => setIdx(i)}
                className={`flex items-start gap-3 p-3 rounded-md cursor-pointer transition-all border ${
                  isLatest 
                    ? `bg-[#0f1422] shadow-lg ${cfg.color.replace('text-', 'border-').replace('400', '500/30')}` 
                    : "bg-[#0a0e1a] border-[#1c2333] opacity-60 hover:opacity-100"
                }`}>
                
                <div className={`mt-0.5 p-1.5 rounded-md border ${cfg.bg} ${cfg.color}`}>
                  {cfg.icon}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start">
                    <span className={`text-[13px] font-medium truncate ${isLatest ? "text-white" : "text-[#c8cdd8]"}`}>
                      {eventLabel}
                    </span>
                    <span className={`text-[10px] mono shrink-0 ml-2 px-1.5 py-0.5 rounded bg-[#151a2e] ${isLatest ? "text-white" : "text-[#4a5468]"}`}>
                      +{item.relative_seconds?.toFixed(1)}s
                    </span>
                  </div>
                  {item.data?.message && (
                    <p className={`text-[11px] mt-1 line-clamp-2 ${isLatest ? "text-[#8892a8]" : "text-[#4a5468]"}`}>
                      {String(item.data.message)}
                    </p>
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
