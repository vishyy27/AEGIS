"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  AreaChart,
  Area,
} from "recharts";

export default function IntelligenceDashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/metrics/decision-intelligence`)
      .then((res) => res.json())
      .then((data) => {
        setMetrics(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load intelligence metrics", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 w-full animate-pulse h-96 flex items-center justify-center">
        <span className="text-slate-400">Loading Intelligence Telemetry...</span>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  // Format data for visualizations
  const weightData = [
    { subject: 'ML Pred', A: metrics?.signal_weights_current?.ml_failure_probability ?? 0, fullMark: 1 },
    { subject: 'Risk Score', A: metrics?.signal_weights_current?.risk_score ?? 0, fullMark: 1 },
    { subject: 'Alerts', A: metrics?.signal_weights_current?.alert_severity ?? 0, fullMark: 1 },
    { subject: 'History', A: metrics?.signal_weights_current?.historical_failure_rate ?? 0, fullMark: 1 },
  ];

  const trendData = (metrics?.confidence?.trend_7d || []).map((val: number, i: number) => ({
    evaluation: `Eval ${i+1}`,
    confidence: val,
  }));

  const anomalyData = [
    { name: 'Spike', value: metrics?.anomaly_summary?.spike_count ?? 0 },
    { name: 'Diverge', value: metrics?.anomaly_summary?.divergence_count ?? 0 },
    { name: 'Reversal', value: metrics?.anomaly_summary?.reversal_count ?? 0 },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 w-full shadow-lg">
      <div className="flex justify-between items-center mb-6 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <span className="bg-blue-500/20 text-blue-400 p-1.5 rounded">🧠</span>
            Adaptive Decision Intelligence
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Meta-Learning Layer (v{metrics.policy_version}) • Evaluated {metrics.model_metrics.evaluated_count} deployments
          </p>
        </div>
        
        <div className="flex gap-4">
          <div className="text-right">
            <div className="text-xs text-slate-500 uppercase tracking-wider">Avg Confidence</div>
            <div className="text-2xl font-bold text-white">{(metrics.confidence.avg * 100).toFixed(1)}%</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-500 uppercase tracking-wider">Drift Risk</div>
            <div className={`text-sm font-bold px-2 py-1 rounded inline-block mt-1 ${
              metrics.drift_status.drift_risk === 'LOW' ? 'bg-emerald-500/20 text-emerald-400' :
              metrics.drift_status.drift_risk === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {metrics.drift_status.drift_risk}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Panel 1: Signal Weights */}
        <div className="bg-slate-800/50 p-4 rounded border border-slate-700/50 flex flex-col items-center">
          <h3 className="text-sm font-medium text-slate-300 mb-2 w-full text-left">Active Signal Weights</h3>
          <div className="w-full h-48">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={weightData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Radar name="Weights" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.4} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Panel 2: Confidence Trend */}
        <div className="bg-slate-800/50 p-4 rounded border border-slate-700/50">
          <h3 className="text-sm font-medium text-slate-300 mb-2">Confidence Trend (Recent)</h3>
          <div className="w-full h-48 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="evaluation" hide />
                <YAxis domain={[0, 1]} hide />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
                  itemStyle={{ color: '#10b981' }}
                />
                <Area type="monotone" dataKey="confidence" stroke="#10b981" fillOpacity={1} fill="url(#colorConfidence)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Panel 3: Stats & Anomalies */}
        <div className="bg-slate-800/50 p-4 rounded border border-slate-700/50 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-3">Model Accuracy Trend</h3>
            <div className="flex gap-2">
              <div className="bg-slate-900 rounded p-3 w-1/2 border border-slate-700/50">
                <div className="text-xs text-slate-500 mb-1">Accuracy</div>
                <div className="text-lg font-bold text-white">{(metrics.model_metrics.accuracy * 100).toFixed(1)}%</div>
              </div>
              <div className="bg-slate-900 rounded p-3 w-1/2 border border-slate-700/50">
                <div className="text-xs text-slate-500 mb-1">Precision</div>
                <div className="text-lg font-bold text-white">{(metrics.model_metrics.precision * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
          
          <div className="mt-4">
            <h3 className="text-sm font-medium text-slate-300 mb-2">Recent Pre-Fail Anomalies</h3>
            <div className="flex gap-1 h-20 items-end w-full">
              {anomalyData.map((a) => (
                <div key={a.name} className="flex-1 flex flex-col items-center group relative">
                  <div 
                    className="w-full bg-indigo-500/80 rounded-t hover:bg-indigo-400 transition-colors"
                    style={{ height: `${Math.max(10, (a.value / 30) * 100)}%` }}
                  ></div>
                  <div className="text-[10px] text-slate-400 mt-1 uppercase">{a.name}</div>
                  <div className="absolute -top-7 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 text-xs px-2 py-1 rounded shadow">
                    {a.value} events
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
      </div>
      
      <div className="mt-4 text-xs text-center justify-center flex items-center text-slate-500 gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
        Updated {new Date(metrics.generated_at).toLocaleTimeString()}
      </div>
    </div>
  );
}
