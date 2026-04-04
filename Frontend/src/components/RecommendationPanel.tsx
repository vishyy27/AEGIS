"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";

export default function RecommendationPanel() {
  return (
    <div className="aegis-card border-l-4 border-l-cyan-500">
      <div className="flex items-center gap-2 mb-4">
        <ShieldCheck className="text-cyan-500" size={20} />
        <h3 className="section-title">AI Recommendation</h3>
      </div>

      <div className="flex items-center gap-3 mb-6 p-4 bg-cyan-500/5 rounded-lg border border-cyan-500/10">
        <div className="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-500">
          <CheckCircle2 size={24} />
        </div>
        <div>
          <div className="text-lg font-bold text-white leading-none mb-1">
            Safe to deploy.
          </div>
          <p className="text-xs text-slate-400">
            Current risk parameters are within acceptable thresholds for
            Production.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-start gap-3">
          <div className="mt-1 text-cyan-500">
            <CheckCircle2 size={14} />
          </div>
          <span className="text-sm text-slate-300">
            Ensure all unit tests pass
          </span>
        </div>
        <div className="flex items-start gap-3">
          <div className="mt-1 text-cyan-500">
            <CheckCircle2 size={14} />
          </div>
          <span className="text-sm text-slate-300">
            Validate staging deployment
          </span>
        </div>
        <div className="flex items-start gap-3">
          <div className="mt-1 text-cyan-500">
            <CheckCircle2 size={14} />
          </div>
          <span className="text-sm text-slate-300">
            Monitor service memory usage
          </span>
        </div>
      </div>
    </div>
  );
}
