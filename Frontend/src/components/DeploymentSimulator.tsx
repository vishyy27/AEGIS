"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Play, RotateCcw, ChevronDown } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface SimResult {
  simulation_id: number;
  results: {
    risk_score: number; risk_level: string; ml_failure_probability: number;
    policy_decision: string; policy_reasoning: string[]; confidence_score: number;
    predicted_alerts: { type: string; severity: string }[]; risk_factors: string[];
  };
}

interface Preset { name: string; description: string; params: Record<string, unknown>; }

const defaults: Record<string, unknown> = {
  commit_count: 5, files_changed: 10, code_churn: 200,
  test_coverage: 80, dependency_updates: 0, historical_failures: 0,
  deployment_frequency: 3, has_db_migration: false, has_auth_changes: false,
};

const fieldLabels: Record<string, string> = {
  commit_count: "Commits", files_changed: "Files Changed", code_churn: "Code Churn",
  test_coverage: "Test Coverage %", dependency_updates: "Dep Updates",
  historical_failures: "Past Failures", deployment_frequency: "Deploy Freq",
  has_db_migration: "DB Migration", has_auth_changes: "Auth Changes",
};

const decisionStyles: Record<string, string> = {
  ALLOW: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  WARN: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  BLOCK: "bg-rose-500/10 text-rose-400 border-rose-500/20",
};

export default function DeploymentSimulator() {
  const [params, setParams] = useState<Record<string, unknown>>(defaults);
  const [result, setResult] = useState<SimResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [showPresets, setShowPresets] = useState(false);

  useEffect(() => {
    fetchAPI<Preset[]>("/api/simulation/presets").then(setPresets).catch(() => {});
  }, []);

  const run = async () => {
    setLoading(true);
    try {
      const res = await fetchAPI<SimResult>("/api/simulation/run", {
        method: "POST", body: JSON.stringify({ ...params, repo_name: "simulation/test" }),
      });
      setResult(res);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      {/* Input */}
      <div className="aegis-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="section-title">Parameters</h3>
          <div className="relative">
            <button onClick={() => setShowPresets(!showPresets)}
              className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors">
              Presets <ChevronDown size={11} />
            </button>
            {showPresets && (
              <div className="absolute right-0 top-5 z-10 w-56 bg-[#0f1422] border border-[#1c2333] rounded-lg shadow-xl overflow-hidden">
                {presets.map(p => (
                  <button key={p.name} onClick={() => { setParams({ ...defaults, ...p.params }); setShowPresets(false); setResult(null); }}
                    className="block w-full text-left px-3 py-2 hover:bg-[#151a2e] transition-colors border-b border-[#1c2333] last:border-0">
                    <span className="text-[12px] text-[#c8cdd8]">{p.name}</span>
                    <span className="block text-[10px] text-[#4a5468]">{p.description}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
          {Object.entries(params).map(([key, val]) => (
            <div key={key}>
              <label className="text-[10px] text-[#4a5468] uppercase tracking-wider block mb-1">
                {fieldLabels[key] || key.replace(/_/g, " ")}
              </label>
              {typeof val === "boolean" ? (
                <button onClick={() => setParams(p => ({ ...p, [key]: !val }))}
                  className={`w-full h-8 rounded-md text-[11px] font-medium border transition-colors ${
                    val ? "bg-blue-500/10 text-blue-400 border-blue-500/20" : "bg-[#151a2e] text-[#4a5468] border-[#1c2333]"
                  }`}>
                  {val ? "Yes" : "No"}
                </button>
              ) : (
                <input type="number" value={Number(val)}
                  onChange={e => setParams(p => ({ ...p, [key]: Number(e.target.value) }))}
                  className="w-full h-8 bg-[#151a2e] border border-[#1c2333] rounded-md px-2.5 text-[12px] text-white outline-none focus:border-blue-500/30 mono transition-colors" />
              )}
            </div>
          ))}
        </div>

        <div className="flex gap-2 mt-4">
          <button onClick={run} disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-md flex items-center justify-center gap-1.5 text-[13px] font-medium transition-colors disabled:opacity-40 active:scale-[0.98]">
            <Play size={14} />{loading ? "Running..." : "Run Simulation"}
          </button>
          <button onClick={() => { setParams(defaults); setResult(null); }}
            className="px-3 py-2 bg-[#151a2e] hover:bg-[#1a2038] text-[#6b7280] rounded-md transition-colors border border-[#1c2333]">
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      {/* Result */}
      {result && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="aegis-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="section-title">Result</h3>
            <span className={`text-[12px] font-semibold px-2.5 py-1 rounded-md border ${
              decisionStyles[result.results.policy_decision] || "bg-[#151a2e] text-[#6b7280] border-[#1c2333]"
            }`}>
              {result.results.policy_decision}
            </span>
          </div>

          <div className="grid grid-cols-4 gap-3 mb-4">
            {[
              { label: "Risk Score", value: `${result.results.risk_score?.toFixed(1)}%`, color: result.results.risk_level === "HIGH" ? "text-rose-400" : "text-[#c8cdd8]" },
              { label: "Risk Level", value: result.results.risk_level, color: result.results.risk_level === "HIGH" ? "text-rose-400" : result.results.risk_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400" },
              { label: "ML Probability", value: `${(result.results.ml_failure_probability * 100).toFixed(1)}%`, color: "text-[#c8cdd8]" },
              { label: "Confidence", value: `${(result.results.confidence_score * 100).toFixed(1)}%`, color: "text-[#c8cdd8]" },
            ].map(m => (
              <div key={m.label} className="bg-[#0a0e1a] rounded-md p-3 border border-[#1c2333]">
                <div className="text-[10px] text-[#4a5468] uppercase tracking-wider">{m.label}</div>
                <div className={`text-[16px] font-semibold mono mt-1 ${m.color}`}>{m.value}</div>
              </div>
            ))}
          </div>

          {result.results.policy_reasoning?.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[10px] text-[#4a5468] uppercase tracking-wider">Reasoning</span>
              {result.results.policy_reasoning.map((r, i) => (
                <p key={i} className="text-[12px] text-[#8892a8] pl-3 border-l border-[#232b3e]">{r}</p>
              ))}
            </div>
          )}

          {result.results.predicted_alerts?.length > 0 && (
            <div className="mt-3 pt-3 border-t border-[#1c2333]">
              <span className="text-[10px] text-[#4a5468] uppercase tracking-wider">Predicted Alerts</span>
              <div className="flex gap-1.5 mt-1.5 flex-wrap">
                {result.results.predicted_alerts.map((a, i) => (
                  <span key={i} className={`text-[10px] px-2 py-0.5 rounded-md border ${
                    a.severity === "CRITICAL" ? "bg-rose-500/10 text-rose-400 border-rose-500/15" : "bg-amber-500/10 text-amber-400 border-amber-500/15"
                  }`}>{a.type}</span>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
