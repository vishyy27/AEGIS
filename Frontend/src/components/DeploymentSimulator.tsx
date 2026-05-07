"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, RotateCcw, ChevronDown, CheckCircle, BrainCircuit, ShieldCheck, BarChart3, Activity } from "lucide-react";
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
  ALLOW: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.15)]",
  WARN: "bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.15)]",
  BLOCK: "bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_10px_rgba(244,63,94,0.15)]",
};

const SIMULATION_STEPS = [
  { id: 1, label: "Ingesting parameters", icon: BarChart3 },
  { id: 2, label: "Running ML risk model", icon: BrainCircuit },
  { id: 3, label: "Evaluating policies", icon: ShieldCheck },
  { id: 4, label: "Finalizing predictions", icon: CheckCircle }
];

export default function DeploymentSimulator() {
  const [params, setParams] = useState<Record<string, unknown>>(defaults);
  const [result, setResult] = useState<SimResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [showPresets, setShowPresets] = useState(false);
  const [mockScore, setMockScore] = useState(0);

  useEffect(() => {
    fetchAPI<Preset[]>("/api/simulation/presets").then(setPresets).catch(() => {});
  }, []);

  useEffect(() => {
    let t: NodeJS.Timeout;
    if (loading) {
      // Animate mock score
      t = setInterval(() => {
        setMockScore(Math.floor(Math.random() * 100));
      }, 150);
    }
    return () => clearInterval(t);
  }, [loading]);

  const run = async () => {
    setLoading(true);
    setResult(null);
    setActiveStep(1);
    
    // Simulate progression for realism
    const interval = setInterval(() => {
      setActiveStep(s => (s < 4 ? s + 1 : s));
    }, 600);

    try {
      const res = await fetchAPI<SimResult>("/api/simulation/run", {
        method: "POST", body: JSON.stringify({ ...params, repo_name: "simulation/test" }),
      });
      // Wait for animation to finish
      setTimeout(() => {
        clearInterval(interval);
        setResult(res);
        setLoading(false);
        setActiveStep(0);
      }, 2400);
    } catch {
      clearInterval(interval);
      setLoading(false);
      setActiveStep(0);
    }
  };

  return (
    <div className="space-y-4">
      {/* Input */}
      <div className="aegis-card relative overflow-hidden">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="section-title text-white flex items-center gap-2">
              <BrainCircuit size={14} className="text-blue-400" />
              Predictive Sandbox
            </h3>
            <p className="text-[11px] text-[#4a5468] mt-1">Adjust parameters to simulate risk outcomes</p>
          </div>
          <div className="relative">
            <button onClick={() => setShowPresets(!showPresets)}
              className="text-[11px] text-blue-400 hover:text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 px-2 py-1 rounded border border-blue-500/20 flex items-center gap-1 transition-colors">
              Presets <ChevronDown size={11} />
            </button>
            {showPresets && (
              <div className="absolute right-0 top-7 z-10 w-56 bg-[#0f1422] border border-[#1c2333] rounded-lg shadow-xl overflow-hidden">
                {presets.map(p => (
                  <button key={p.name} onClick={() => { setParams({ ...defaults, ...p.params }); setShowPresets(false); setResult(null); }}
                    className="block w-full text-left px-3 py-2 hover:bg-[#151a2e] transition-colors border-b border-[#1c2333] last:border-0">
                    <span className="text-[12px] text-[#c8cdd8] font-medium">{p.name}</span>
                    <span className="block text-[10px] text-[#4a5468] mt-0.5">{p.description}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {Object.entries(params).map(([key, val]) => (
            <div key={key}>
              <label className="text-[10px] text-[#4a5468] uppercase tracking-wider block mb-1.5 font-medium">
                {fieldLabels[key] || key.replace(/_/g, " ")}
              </label>
              {typeof val === "boolean" ? (
                <button onClick={() => setParams(p => ({ ...p, [key]: !val }))}
                  className={`w-full h-8 rounded-md text-[11px] font-medium border transition-colors ${
                    val ? "bg-blue-500/15 text-blue-400 border-blue-500/30 shadow-[inset_0_1px_3px_rgba(59,130,246,0.1)]" : "bg-[#0a0e1a] hover:bg-[#151a2e] text-[#6b7280] border-[#1c2333]"
                  }`}>
                  {val ? "Yes" : "No"}
                </button>
              ) : (
                <div className="relative group">
                  <input type="number" value={Number(val)}
                    onChange={e => setParams(p => ({ ...p, [key]: Number(e.target.value) }))}
                    className="w-full h-8 bg-[#0a0e1a] hover:bg-[#151a2e] border border-[#1c2333] rounded-md px-2.5 text-[12px] text-white outline-none focus:bg-[#0f1422] focus:border-blue-500/40 focus:ring-1 focus:ring-blue-500/10 mono transition-colors" />
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="flex gap-2 mt-5 pt-5 border-t border-[#1c2333]">
          <button onClick={run} disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-md flex items-center justify-center gap-1.5 text-[13px] font-medium transition-colors disabled:opacity-40 active:scale-[0.98] shadow-lg shadow-blue-900/20">
            <Play size={14} />{loading ? "Simulating..." : "Run Simulation"}
          </button>
          <button onClick={() => { setParams(defaults); setResult(null); }} disabled={loading}
            className="px-3 py-2 bg-[#0a0e1a] hover:bg-[#151a2e] text-[#6b7280] hover:text-[#c8cdd8] disabled:opacity-40 rounded-md transition-colors border border-[#1c2333]">
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      {/* Progression Animation */}
      <AnimatePresence>
        {loading && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <div className="aegis-card py-6 flex flex-col items-center justify-center">
              <div className="flex items-center justify-center gap-8 mb-6">
                {SIMULATION_STEPS.map((step, i) => {
                  const Icon = step.icon;
                  const isActive = activeStep >= step.id;
                  const isCurrent = activeStep === step.id;
                  return (
                    <div key={step.id} className="flex flex-col items-center relative">
                      {i < SIMULATION_STEPS.length - 1 && (
                        <div className={`absolute top-5 left-10 w-16 h-[1px] ${isActive ? 'bg-blue-500/50' : 'bg-[#1c2333]'} transition-colors duration-500`} />
                      )}
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 z-10 transition-all duration-500 ${
                        isActive ? 'bg-[#0f1422] border-blue-500 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.3)]' : 'bg-[#0a0e1a] border-[#1c2333] text-[#4a5468]'
                      }`}>
                        <Icon size={16} className={isCurrent ? 'animate-pulse' : ''} />
                      </div>
                      <span className={`text-[10px] mt-2 absolute top-12 w-24 text-center ${isActive ? 'text-[#c8cdd8]' : 'text-[#4a5468]'}`}>{step.label}</span>
                    </div>
                  );
                })}
              </div>
              <div className="mt-8 text-center">
                <span className="text-[10px] text-[#4a5468] uppercase tracking-wider block mb-1">Model Volatility</span>
                <span className="text-3xl font-bold text-white mono opacity-50 blur-[1px]">{mockScore}%</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Result */}
      {result && !loading && (
        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="aegis-card border-blue-500/20 bg-[#0a0e1a] relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-[0.03] pointer-events-none">
            <BrainCircuit size={200} />
          </div>
          
          <div className="flex items-center justify-between mb-5 relative z-10">
            <div>
              <h3 className="section-title text-white">Simulation Outcome</h3>
              <p className="text-[11px] text-[#8892a8] mt-0.5">Based on ML evaluation and policy enforcement</p>
            </div>
            <span className={`text-[13px] font-bold px-3 py-1.5 rounded-md border tracking-wide uppercase ${
              decisionStyles[result.results.policy_decision] || "bg-[#151a2e] text-[#6b7280] border-[#1c2333]"
            }`}>
              {result.results.policy_decision}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6 relative z-10">
            {[
              { label: "Risk Score", value: `${result.results.risk_score?.toFixed(1)}%`, color: result.results.risk_level === "HIGH" ? "text-rose-400" : result.results.risk_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400" },
              { label: "Risk Level", value: result.results.risk_level, color: result.results.risk_level === "HIGH" ? "text-rose-400" : result.results.risk_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400" },
              { label: "ML Probability", value: `${(result.results.ml_failure_probability * 100).toFixed(1)}%`, color: "text-[#e2e8f0]" },
              { label: "Confidence", value: `${(result.results.confidence_score * 100).toFixed(1)}%`, color: "text-[#e2e8f0]" },
            ].map((m, i) => (
              <motion.div key={m.label} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                className="bg-[#0f1422] rounded-md p-3.5 border border-[#1c2333] shadow-[inset_0_1px_3px_rgba(0,0,0,0.2)]">
                <div className="text-[10px] text-[#4a5468] uppercase tracking-wider">{m.label}</div>
                <div className={`text-xl font-bold mono mt-1 ${m.color}`}>{m.value}</div>
              </motion.div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
            {result.results.policy_reasoning?.length > 0 && (
              <div className="bg-[#0f1422] border border-[#1c2333] rounded-md p-4">
                <span className="text-[10px] text-[#4a5468] uppercase tracking-wider flex items-center gap-1.5 mb-2.5">
                  <ShieldCheck size={12} className="text-[#8892a8]" />
                  Policy Reasoning
                </span>
                <div className="space-y-2">
                  {result.results.policy_reasoning.map((r, i) => (
                    <div key={i} className="flex gap-2 text-[12px] text-[#c8cdd8]">
                      <span className="text-[#4a5468] mt-0.5">•</span>
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.results.predicted_alerts?.length > 0 && (
              <div className="bg-[#0f1422] border border-[#1c2333] rounded-md p-4">
                <span className="text-[10px] text-[#4a5468] uppercase tracking-wider flex items-center gap-1.5 mb-2.5">
                  <Activity size={12} className="text-[#8892a8]" />
                  Predicted Alerts
                </span>
                <div className="flex gap-2 flex-wrap">
                  {result.results.predicted_alerts.map((a, i) => (
                    <span key={i} className={`text-[11px] font-medium px-2 py-1 rounded border ${
                      a.severity === "CRITICAL" ? "bg-rose-500/10 text-rose-400 border-rose-500/20" : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    }`}>{a.type}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}
