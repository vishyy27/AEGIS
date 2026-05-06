"use client";

import { useEffect, useState } from "react";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import { fetchAPI } from "@/lib/api";

export default function IntelligenceDashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI("/api/metrics/decision-intelligence")
      .then(setMetrics)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="aegis-card h-full">
        <div className="space-y-3">
          <div className="h-4 w-48 bg-[#151a2e] rounded animate-pulse" />
          <div className="grid grid-cols-3 gap-3">
            {[1,2,3].map(i => <div key={i} className="h-44 bg-[#151a2e] rounded-md animate-pulse" />)}
          </div>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const weightData = [
    { subject: "ML Pred", A: metrics?.signal_weights_current?.ml_failure_probability ?? 0 },
    { subject: "Risk Score", A: metrics?.signal_weights_current?.risk_score ?? 0 },
    { subject: "Alerts", A: metrics?.signal_weights_current?.alert_severity ?? 0 },
    { subject: "History", A: metrics?.signal_weights_current?.historical_failure_rate ?? 0 },
  ];

  const trendData = (metrics?.confidence?.trend_7d || []).map((val: number, i: number) => ({
    idx: i + 1,
    confidence: val,
  }));

  const anomalyData = [
    { name: "Spike", count: metrics?.anomaly_summary?.spike_count ?? 0 },
    { name: "Diverge", count: metrics?.anomaly_summary?.divergence_count ?? 0 },
    { name: "Reversal", count: metrics?.anomaly_summary?.reversal_count ?? 0 },
  ];

  const driftRisk = metrics?.drift_status?.drift_risk ?? "LOW";

  return (
    <div className="aegis-card h-full">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="section-title">Decision Intelligence</h3>
          <p className="text-[11px] text-[#3d4454] mt-0.5">
            Policy v{metrics?.policy_version ?? "—"} · {metrics?.model_metrics?.evaluated_count ?? 0} evaluated
          </p>
        </div>
        <div className="flex gap-3">
          <div className="text-right">
            <div className="text-[10px] text-[#4a5468] uppercase tracking-wider">Confidence</div>
            <div className="text-[16px] font-semibold text-white mono">{((metrics?.confidence?.avg ?? 0) * 100).toFixed(1)}%</div>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-[#4a5468] uppercase tracking-wider">Drift</div>
            <span className={`text-[11px] font-semibold px-1.5 py-0.5 rounded inline-block mt-0.5 ${
              driftRisk === "LOW" ? "bg-emerald-500/10 text-emerald-400" :
              driftRisk === "MEDIUM" ? "bg-amber-500/10 text-amber-400" :
              "bg-rose-500/10 text-rose-400"
            }`}>{driftRisk}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Radar */}
        <div className="bg-[#0a0e1a] border border-[#1c2333] p-3 rounded-md">
          <span className="text-[10px] text-[#4a5468] uppercase tracking-wider">Signal Weights</span>
          <div className="w-full h-40 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={weightData}>
                <PolarGrid stroke="#1c2333" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: "#4a5468", fontSize: 10 }} />
                <Radar dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Confidence Trend */}
        <div className="bg-[#0a0e1a] border border-[#1c2333] p-3 rounded-md">
          <span className="text-[10px] text-[#4a5468] uppercase tracking-wider">Confidence Trend</span>
          <div className="w-full h-40 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="cGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="idx" hide />
                <YAxis domain={[0, 1]} hide />
                <Tooltip contentStyle={{ backgroundColor: "#0f1422", border: "1px solid #1c2333", fontSize: "11px", borderRadius: "6px" }} />
                <Area type="monotone" dataKey="confidence" stroke="#22c55e" fill="url(#cGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Stats & Anomalies */}
        <div className="bg-[#0a0e1a] border border-[#1c2333] p-3 rounded-md flex flex-col justify-between">
          <div>
            <span className="text-[10px] text-[#4a5468] uppercase tracking-wider">Model Metrics</span>
            <div className="grid grid-cols-2 gap-2 mt-2">
              <div className="bg-[#0f1422] rounded p-2 border border-[#1c2333]">
                <div className="text-[9px] text-[#3d4454]">Accuracy</div>
                <div className="text-[14px] font-semibold text-white mono">{((metrics?.model_metrics?.accuracy ?? 0) * 100).toFixed(1)}%</div>
              </div>
              <div className="bg-[#0f1422] rounded p-2 border border-[#1c2333]">
                <div className="text-[9px] text-[#3d4454]">Precision</div>
                <div className="text-[14px] font-semibold text-white mono">{((metrics?.model_metrics?.precision ?? 0) * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>

          <div className="mt-3">
            <span className="text-[10px] text-[#4a5468] uppercase tracking-wider">Anomalies</span>
            <div className="flex gap-1 h-14 items-end w-full mt-2">
              {anomalyData.map(a => {
                const h = Math.max(8, (a.count / 30) * 100);
                return (
                  <div key={a.name} className="flex-1 flex flex-col items-center group">
                    <div className="w-full bg-blue-500/40 hover:bg-blue-500/60 rounded-t transition-colors" style={{ height: `${h}%` }} />
                    <div className="text-[8px] text-[#3d4454] mt-1 uppercase">{a.name}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-3 text-center">
        <span className="text-[10px] text-[#3d4454] flex items-center justify-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-live-dot" />
          Updated {metrics?.generated_at ? new Date(metrics.generated_at).toLocaleTimeString() : "—"}
        </span>
      </div>
    </div>
  );
}
