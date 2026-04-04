"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface Deployment {
  id: string;
  service: string;
  environment: string;
  riskScore: number;
  status: "Successful" | "Failed" | "In Progress";
  timestamp: string;
}

const deployments: Deployment[] = [
  {
    id: "DEP-9421",
    service: "auth-service",
    environment: "Production",
    riskScore: 12,
    status: "Successful",
    timestamp: "10 min ago",
  },
  {
    id: "DEP-9420",
    service: "payment-api",
    environment: "Production",
    riskScore: 45,
    status: "In Progress",
    timestamp: "25 min ago",
  },
  {
    id: "DEP-9419",
    service: "inventory-ui",
    environment: "Staging",
    riskScore: 8,
    status: "Successful",
    timestamp: "1 hour ago",
  },
  {
    id: "DEP-9418",
    service: "gateway-node",
    environment: "Production",
    riskScore: 78,
    status: "Failed",
    timestamp: "3 hours ago",
  },
  {
    id: "DEP-9417",
    service: "auth-service",
    environment: "Staging",
    riskScore: 15,
    status: "Successful",
    timestamp: "5 hours ago",
  },
];

export default function DeploymentTable({ limit }: { limit?: number }) {
  const displayData = limit ? deployments.slice(0, limit) : deployments;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="pb-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              ID
            </th>
            <th className="pb-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Service
            </th>
            <th className="pb-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Env
            </th>
            <th className="pb-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Risk
            </th>
            <th className="pb-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Status
            </th>
            <th className="pb-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">
              Time
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50">
          {displayData.map((dep) => (
            <tr
              key={dep.id}
              className="group hover:bg-slate-800/20 transition-colors cursor-pointer"
            >
              <td className="py-4 text-sm font-medium text-slate-300">
                {dep.id}
              </td>
              <td className="py-4 text-sm text-white font-medium">
                {dep.service}
              </td>
              <td className="py-4">
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400 uppercase tracking-tighter">
                  {dep.environment}
                </span>
              </td>
              <td className="py-4">
                <div className="flex items-center gap-2">
                  <div
                    className="w-1.5 h-1.5 rounded-full"
                    style={{
                      backgroundColor:
                        dep.riskScore > 70
                          ? "#ef4444"
                          : dep.riskScore > 30
                            ? "#f59e0b"
                            : "#06b6d4",
                    }}
                  />
                  <span className="text-sm font-bold text-white">
                    {dep.riskScore}%
                  </span>
                </div>
              </td>
              <td className="py-4">
                <span
                  className={cn(
                    "text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-tighter",
                    dep.status === "Successful"
                      ? "bg-emerald-500/10 text-emerald-500"
                      : dep.status === "Failed"
                        ? "bg-rose-500/10 text-rose-500"
                        : "bg-amber-500/10 text-amber-500",
                  )}
                >
                  {dep.status}
                </span>
              </td>
              <td className="py-4 text-sm text-slate-500 text-right">
                {dep.timestamp}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
