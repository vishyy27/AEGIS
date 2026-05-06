"use client";

import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Plus, ShieldCheck } from "lucide-react";

import StatCard from "@/components/StatCard";
import RiskChart from "@/components/RiskChart";
import RiskFactors from "@/components/RiskFactors";
import RecommendationPanel from "@/components/RecommendationPanel";
import DeploymentTable from "@/components/DeploymentTable";
import IntelligenceDashboard from "@/components/IntelligenceDashboard";
import LiveTelemetryFeed from "@/components/LiveTelemetryFeed";
import { fetchAPI } from "@/lib/api";

interface SummaryData {
  globalRiskScore: number;
  activeOutages: number;
  successRate: number;
  riskTrend: number[];
  riskFactors: { factor: string; impact: string }[];
}

export default function Dashboard() {
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<SummaryData>("/api/dashboard/summary")
      .then(setSummary)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-5">
        <div className="h-5 w-48 bg-[#151a2e] rounded animate-pulse" />
        <div className="grid grid-cols-3 gap-4">
          {[1,2,3].map(i => <div key={i} className="h-28 bg-[#0f1422] rounded-lg border border-[#1c2333] animate-pulse" />)}
        </div>
        <div className="h-64 bg-[#0f1422] rounded-lg border border-[#1c2333] animate-pulse" />
      </div>
    );
  }

  const riskScore = summary?.globalRiskScore ?? 0;
  const riskLevel = riskScore > 70 ? "HIGH" : riskScore > 40 ? "MEDIUM" : "LOW";
  const riskColor = riskScore > 70 ? "#ef4444" : riskScore > 40 ? "#eab308" : "#22c55e";

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="page-title">Deployment Intelligence</h1>
          <p className="text-muted mt-0.5">Real-time risk analysis across CI/CD pipelines</p>
        </div>
        <button className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-md flex items-center gap-1.5 text-[13px] font-medium transition-colors active:scale-[0.98]">
          <Plus size={15} />
          New Analysis
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Risk Score"
          value={`${riskScore}%`}
          status={riskLevel}
          statusColor={riskColor}
          icon={ShieldCheck}
        />
        <StatCard
          title="Active Incidents"
          value={(summary?.activeOutages ?? 0).toString()}
          subtitle={summary?.activeOutages === 0 ? "All systems nominal" : undefined}
          icon={AlertCircle}
        />
        <StatCard
          title="Success Rate"
          value={`${summary?.successRate ?? 0}%`}
          subtitle="Last 30 days"
          icon={CheckCircle2}
        />
      </div>

      {/* Risk Chart + Factors */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <RiskChart data={summary?.riskTrend || []} />
        </div>
        <div className="lg:col-span-1">
          <RiskFactors factors={summary?.riskFactors || []} />
        </div>
      </div>

      {/* Intelligence + Live Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <IntelligenceDashboard />
        </div>
        <div className="lg:col-span-1">
          <LiveTelemetryFeed />
        </div>
      </div>

      {/* Recommendations + Deployments */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1">
          <RecommendationPanel />
        </div>
        <div className="lg:col-span-2">
          <div className="aegis-card">
            <div className="flex justify-between items-center mb-4">
              <h3 className="section-title">Recent Deployments</h3>
              <button className="text-[12px] text-blue-400 hover:text-blue-300 font-medium transition-colors">
                View all
              </button>
            </div>
            <DeploymentTable limit={5} />
          </div>
        </div>
      </div>
    </div>
  );
}
