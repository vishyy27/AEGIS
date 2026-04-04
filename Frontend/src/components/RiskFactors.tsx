"use client";

import React from "react";

// ✅ ADD THIS TYPE
type BackendFactor = {
  factor: string;
  impact: string;
};

// ✅ ADD PROPS
interface Props {
  factors: BackendFactor[];
}

interface FactorProps {
  label: string;
  value: number;
  color: string;
}

const Factor = ({ label, value, color }: FactorProps) => (
  <div className="space-y-2">
    <div className="flex justify-between text-xs font-medium">
      <span className="text-slate-400 uppercase tracking-tighter">{label}</span>
      <span className="text-white">{value}%</span>
    </div>
    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-1000"
        style={{ width: `${value}%`, backgroundColor: color }}
      />
    </div>
  </div>
);

// ✅ MODIFY FUNCTION SIGNATURE ONLY
export default function RiskFactors({ factors = [] }: Props) {
  // ✅ CONVERT BACKEND DATA → UI FORMAT
  const parsedFactors = factors.map((item) => {
    const value = parseInt(item.impact.replace("%", "").replace("+", ""));

    return {
      label: item.factor,
      value,
      color: value > 70 ? "#ef4444" : value > 40 ? "#f59e0b" : "#06b6d4",
    };
  });

  return (
    <div className="aegis-card h-full flex flex-col justify-center">
      <h3 className="text-sm font-semibold text-slate-300 mb-6 flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse" />
        AI RISK FACTORS
      </h3>

      <div className="space-y-5">
        {/* ✅ USE DYNAMIC DATA */}
        {parsedFactors.length > 0 ? (
          parsedFactors.map((f, index) => (
            <Factor
              key={index}
              label={f.label}
              value={f.value}
              color={f.color}
            />
          ))
        ) : (
          <p className="text-slate-400 text-sm">No data available</p>
        )}
      </div>
    </div>
  );
}
