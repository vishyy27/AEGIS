"use client";

import React from "react";
import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    isUp: boolean;
  };
  status?: string;
  statusColor?: string;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  status,
  statusColor,
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="aegis-card group hover:border-slate-700 transition-colors"
    >
      <div className="flex justify-between items-start mb-4">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {title}
        </span>
        {Icon && (
          <Icon
            size={18}
            className="text-slate-500 group-hover:text-cyan-500 transition-colors"
          />
        )}
      </div>

      <div className="flex items-baseline gap-3 mb-1">
        <h2 className="text-4xl font-bold text-white tracking-tight">
          {value}
        </h2>
        {trend && (
          <span
            className={cn(
              "text-xs font-bold",
              trend.isUp ? "text-emerald-500" : "text-rose-500",
            )}
          >
            {trend.isUp ? "↑" : "↓"} {Math.abs(trend.value)}%
          </span>
        )}
      </div>

      {status && (
        <div
          className="text-[10px] font-bold px-2 py-0.5 rounded inline-block mb-1 tracking-wider uppercase"
          style={{
            backgroundColor: `${statusColor}22` || "rgba(59, 130, 246, 0.1)",
            color: statusColor || "var(--primary)",
          }}
        >
          {status}
        </div>
      )}

      {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
    </motion.div>
  );
}
