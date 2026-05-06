"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { FlaskConical, Play, RotateCcw, ChevronDown } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface SimResult {
  simulation_id: number;
  simulation_name: string;
  results: {
    risk_score: number;
    risk_level: string;
    ml_failure_probability: number;
    policy_decision: string;
    policy_reasoning: string[];
    confidence_score: number;
    predicted_alerts: { type: string; severity: string }[];
    risk_factors: string[];
  };
}

interface Preset { name: string; description: string; params: Record<string, unknown>; }

const defaultParams = {
  repo_name: "simulation/test-service",
  commit_count: 5, files_changed: 10, code_churn: 200,
  test_coverage: 80, dependency_updates: 0, historical_failures: 0,
  deployment_frequency: 3, has_db_migration: false, has_auth_changes: false,
};

export default function DeploymentSimulator() {
  const [params, setParams] = useState<Record<string, unknown>>(defaultParams);
  const [result, setResult] = useState<SimResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [showPresets, setShowPresets] = useState(false);

  React.useEffect(() => {
    fetchAPI<Preset[]>("/api/simulation/presets").then(setPresets).catch(() => {});
  }, []);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetchAPI<SimResult>("/api/simulation/run", {
        method: "POST", body: JSON.stringify(params),
      });
      setResult(res);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const applyPreset = (preset: Preset) => {
    setParams({ ...defaultParams, ...preset.params });
    setShowPresets(false);
    setResult(null);
  };

  const decisionColors: Record<string, string> = {
    ALLOW: "from-emerald-600 to-emerald-800", WARN: "from-amber-600 to-amber-800", BLOCK: "from-red-600 to-red-800",
  };

  return (
    <div className="space-y-6">
      {/* Input Panel */}
      <div className="aegis-card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <FlaskConical size={18} className="text-violet-400" />
            <h3 className="section-title">Simulation Parameters</h3>
          </div>
          <div className="relative">
            <button onClick={() => setShowPresets(!showPresets)} className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
              Load Preset <ChevronDown size={12} />
            </button>
            {showPresets && (
              <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} className="absolute right-0 top-6 z-10 w-64 bg-slate-900 border border-slate-700 rounded-lg shadow-xl overflow-hidden">
                {presets.map(p => (
                  <button key={p.name} onClick={() => applyPreset(p)} className="block w-full text-left px-4 py-2.5 hover:bg-slate-800 transition-colors border-b border-slate-800 last:border-0">
                    <span className="text-sm text-slate-200">{p.name}</span>
                    <span className="block text-[10px] text-slate-500">{p.description}</span>
                  </button>
                ))}
              </motion.div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(params).filter(([k]) => k !== "repo_name").map(([key, val]) => (
            <div key={key}>
              <label className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 block">
                {key.replace(/_/g, " ")}
              </label>
              {typeof val === "boolean" ? (
                <button
                  onClick={() => setParams(p => ({ ...p, [key]: !val }))}
                  className={`w-full h-9 rounded-lg text-xs font-medium transition-colors ${val ? "bg-cyan-600/20 text-cyan-400 border border-cyan-500/30" : "bg-slate-800 text-slate-500 border border-slate-700"}`}
                >
                  {val ? "Yes" : "No"}
                </button>
              ) : (
                <input
                  type="number" value={Number(val)} step={key === "test_coverage" ? 5 : 1}
                  onChange={e => setParams(p => ({ ...p, [key]: Number(e.target.value) }))}
                  className="w-full h-9 bg-slate-800 border border-slate-700 rounded-lg px-3 text-sm text-white outline-none focus:border-cyan-500/50 mono"
                />
              )}
            </div>
          ))}
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={runSimulation} disabled={loading}
            className="flex-1 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white py-2.5 rounded-lg flex items-center justify-center gap-2 font-semibold text-sm transition-all disabled:opacity-50 active:scale-[0.98]">
            <Play size={16} />{loading ? "Running..." : "Run Simulation"}
          </button>
          <button onClick={() => { setParams(defaultParams); setResult(null); }}
            className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors">
            <RotateCcw size={16} />
          </button>
        </div>
      </div>

      {/* Results Panel */}
      {result && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="aegis-card glow-purple">
          <h3 className="section-title mb-4">Simulation Results</h3>

          {/* Decision Banner */}
          <div className={`bg-gradient-to-r ${decisionColors[result.results.policy_decision] || "from-slate-700 to-slate-800"} rounded-xl p-5 mb-6`}>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs text-white/60 uppercase tracking-wider">Policy Decision</span>
                <h2 className="text-3xl font-bold text-white mt-1">{result.results.policy_decision}</h2>
              </div>
              <div className="text-right">
                <div className="text-xs text-white/60">Risk Score</div>
                <div className="text-2xl font-bold text-white mono">{result.results.risk_score?.toFixed(1)}%</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-slate-900/50 rounded-lg p-3 text-center">
              <div className="text-[10px] text-slate-500 uppercase">ML Probability</div>
              <div className="text-lg font-bold text-white mono mt-1">{(result.results.ml_failure_probability * 100).toFixed(1)}%</div>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-3 text-center">
              <div className="text-[10px] text-slate-500 uppercase">Confidence</div>
              <div className="text-lg font-bold text-white mono mt-1">{(result.results.confidence_score * 100).toFixed(1)}%</div>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-3 text-center">
              <div className="text-[10px] text-slate-500 uppercase">Risk Level</div>
              <div className={`text-lg font-bold mt-1 ${result.results.risk_level === "HIGH" ? "text-red-400" : result.results.risk_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400"}`}>
                {result.results.risk_level}
              </div>
            </div>
          </div>

          {result.results.policy_reasoning?.length > 0 && (
            <div className="mb-4">
              <span className="text-xs text-slate-500 font-medium">Reasoning:</span>
              <ul className="mt-1 space-y-1">
                {result.results.policy_reasoning.map((r, i) => (
                  <li key={i} className="text-xs text-slate-400 pl-3 border-l-2 border-slate-700">{r}</li>
                ))}
              </ul>
            </div>
          )}

          {result.results.predicted_alerts?.length > 0 && (
            <div>
              <span className="text-xs text-slate-500 font-medium">Predicted Alerts:</span>
              <div className="flex gap-2 mt-1 flex-wrap">
                {result.results.predicted_alerts.map((a, i) => (
                  <span key={i} className={`text-[10px] px-2 py-0.5 rounded ${a.severity === "CRITICAL" ? "bg-red-500/10 text-red-400" : "bg-amber-500/10 text-amber-400"}`}>
                    {a.type}
                  </span>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
