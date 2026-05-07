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
    <div className="aegis-card relative overflow-hidden group">
      {/* Background ambient glow based on status if provided */}
      {statusColor && (
        <div 
          className="absolute -top-10 -right-10 w-24 h-24 rounded-full blur-2xl opacity-10 transition-opacity duration-500 group-hover:opacity-20"
          style={{ backgroundColor: statusColor }}
        />
      )}

      <div className="flex items-center justify-between mb-4 relative z-10">
        <span className="text-[10px] font-semibold text-[#8892a8] uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className="p-1.5 bg-[#0a0e1a] border border-[#1c2333] rounded-md transition-colors group-hover:border-[#232b3e]">
            <Icon size={12} className="text-[#6b7280]" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2.5 relative z-10">
        <span className="text-3xl font-bold text-white tracking-tight mono">{value}</span>
        {trend && (
          <span className={`flex items-center gap-0.5 text-[11px] font-medium px-1.5 py-0.5 rounded-sm ${
            trend.isUp ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"
          }`}>
            {trend.isUp ? "↑" : "↓"} {Math.abs(trend.value)}%
          </span>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between relative z-10 h-4">
        {status ? (
          <span className="inline-flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border"
            style={{ backgroundColor: `${statusColor}10`, color: statusColor, borderColor: `${statusColor}20` }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColor }} />
            {status}
          </span>
        ) : <div />}
        
        {subtitle && <p className="text-[10px] text-[#4a5468] font-medium">{subtitle}</p>}
      </div>
    </div>
  );
}
