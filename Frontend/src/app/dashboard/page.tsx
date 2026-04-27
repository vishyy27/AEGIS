"use client";

import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Plus, ShieldCheck } from "lucide-react";

import StatCard from "@/components/StatCard";
import RiskChart from "@/components/RiskChart";
import RiskFactors from "@/components/RiskFactors";
import RecommendationPanel from "@/components/RecommendationPanel";
import DeploymentTable from "@/components/DeploymentTable";
import IntelligenceDashboard from "@/components/IntelligenceDashboard";

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
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/dashboard/summary`)
      .then((res) => res.json())
      .then((data) => {
        console.log("API DATA:", data);
        setSummary(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  // 🔥 Loading UI
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-lg text-muted">
        Loading dashboard...
      </div>
    );
  }

  // 🔥 Dynamic Risk Level
  const riskLevel =
    (summary?.globalRiskScore ?? 0) > 70
      ? "HIGH RISK"
      : (summary?.globalRiskScore ?? 0) > 40
        ? "MEDIUM RISK"
        : "LOW RISK";

  const riskColor =
    (summary?.globalRiskScore ?? 0) > 70
      ? "#ef4444"
      : (summary?.globalRiskScore ?? 0) > 40
        ? "#f59e0b"
        : "#06b6d4";

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title mb-1">Deployment Risk Prediction</h1>
          <p className="text-muted">
            Real-time AI analysis of CI/CD pipelines and code changes.
          </p>
        </div>

        <button className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white px-5 py-2.5 rounded-lg flex items-center gap-2 font-semibold text-sm transition-all shadow-lg shadow-cyan-900/20 active:scale-95">
          <Plus size={18} />
          Analyze New Deployment
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Global Risk Score"
          value={`${summary?.globalRiskScore ?? 0}%`}
          status={riskLevel}
          statusColor={riskColor}
          icon={ShieldCheck}
          trend={{ value: 12, isUp: false }}
        />

        <StatCard
          title="Active Outages"
          value={(summary?.activeOutages ?? 0).toString()}
          subtitle="All systems nominal"
          icon={AlertCircle}
        />

        <StatCard
          title="Success Rate"
          value={`${summary?.successRate ?? 0}%`}
          subtitle="Last 30 days"
          icon={CheckCircle2}
          trend={{ value: 0.2, isUp: true }}
        />
      </div>

      {/* Charts + Factors */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RiskChart data={summary?.riskTrend || []} />
        </div>

        <div className="lg:col-span-1">
          <RiskFactors factors={summary?.riskFactors || []} />
        </div>
      </div>

      {/* Advanced Intelligence Telemetry */}
      <div className="w-full">
        <IntelligenceDashboard />
      </div>

      {/* Recommendations + Deployments */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <RecommendationPanel />
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="aegis-card">
            <div className="flex justify-between items-center mb-6">
              <h3 className="section-title">Recent Deployments</h3>
              <button className="text-xs text-cyan-400 font-medium hover:underline">
                View All
              </button>
            </div>

            <DeploymentTable limit={5} />
          </div>
        </div>
      </div>
    </div>
  );
}
