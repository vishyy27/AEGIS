"use client";

import React from "react";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: { value: number; isUp: boolean };
  status?: string;
  statusColor?: string;
}

export default function StatCard({ title, value, subtitle, icon: Icon, trend, status, statusColor }: StatCardProps) {
  return (
    <div className="aegis-card">
      <div className="flex items-center justify-between mb-3">
        <span className="label">{title}</span>
        {Icon && <Icon size={15} className="text-[#3d4454]" />}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold text-white tracking-tight mono">{value}</span>
        {trend && (
          <span className={`text-[11px] font-medium ${trend.isUp ? "text-emerald-400" : "text-rose-400"}`}>
            {trend.isUp ? "↑" : "↓"} {Math.abs(trend.value)}%
          </span>
        )}
      </div>

      {status && (
        <span className="inline-block mt-2 text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded"
          style={{ backgroundColor: `${statusColor}15`, color: statusColor }}>
          {status}
        </span>
      )}
      {subtitle && <p className="text-[12px] text-[#4a5468] mt-1">{subtitle}</p>}
    </div>
  );
}
