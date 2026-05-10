"use client";

import React from "react";

interface SkeletonProps {
  variant?: "card" | "table" | "chart" | "text" | "stat";
  rows?: number;
  className?: string;
}

function SkeletonPulse({ className = "" }: { className?: string }) {
  return <div className={`bg-[#151a2e] rounded animate-pulse ${className}`} />;
}

export default function SkeletonLoader({ variant = "card", rows = 3, className = "" }: SkeletonProps) {
  switch (variant) {
    case "stat":
      return (
        <div className={`aegis-card space-y-3 ${className}`}>
          <SkeletonPulse className="h-3 w-20" />
          <SkeletonPulse className="h-8 w-28" />
          <SkeletonPulse className="h-2.5 w-16" />
        </div>
      );

    case "chart":
      return (
        <div className={`aegis-card ${className}`}>
          <SkeletonPulse className="h-4 w-32 mb-4" />
          <SkeletonPulse className="h-48 w-full rounded-md" />
        </div>
      );

    case "table":
      return (
        <div className={`space-y-1 ${className}`}>
          {Array.from({ length: rows }).map((_, i) => (
            <SkeletonPulse key={i} className="h-12 w-full rounded-md border border-[#1c2333]" />
          ))}
        </div>
      );

    case "text":
      return (
        <div className={`space-y-2 ${className}`}>
          {Array.from({ length: rows }).map((_, i) => (
            <SkeletonPulse key={i} className={`h-3 ${i === rows - 1 ? "w-2/3" : "w-full"}`} />
          ))}
        </div>
      );

    default:
      return (
        <div className={`aegis-card space-y-3 ${className}`}>
          <SkeletonPulse className="h-4 w-32" />
          <SkeletonPulse className="h-20 w-full rounded-md" />
          <SkeletonPulse className="h-3 w-24" />
        </div>
      );
  }
}
