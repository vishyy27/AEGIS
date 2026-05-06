"use client";

import React from "react";

interface Props {
  factors: { factor: string; impact: string }[];
}

export default function RiskFactors({ factors = [] }: Props) {
  const parsed = factors.map(item => {
    const value = parseInt(item.impact?.replace(/[^0-9]/g, "") || "0") || 0;
    return {
      label: item.factor,
      value,
      color: value > 70 ? "#ef4444" : value > 40 ? "#eab308" : "#3b82f6",
    };
  });

  return (
    <div className="aegis-card h-full flex flex-col">
      <h3 className="section-title mb-4">Risk Factors</h3>

      {parsed.length > 0 ? (
        <div className="space-y-3">
          {parsed.map((f, i) => (
            <div key={i}>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#8892a8]">{f.label}</span>
                <span className="text-[#c8cdd8] mono">{f.value}%</span>
              </div>
              <div className="h-1 w-full bg-[#1c2333] rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-700" style={{ width: `${f.value}%`, backgroundColor: f.color }} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[12px] text-[#3d4454]">No data available</p>
      )}
    </div>
  );
}
