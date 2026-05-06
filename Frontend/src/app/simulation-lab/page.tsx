"use client";

import React from "react";
import { FlaskConical } from "lucide-react";
import DeploymentSimulator from "@/components/DeploymentSimulator";

export default function SimulationLabPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title text-gradient-purple flex items-center gap-3">
          <FlaskConical size={28} className="text-violet-400" />
          Simulation Lab
        </h1>
        <p className="text-muted mt-1">
          Test synthetic deployments against the real ML + Policy engine before releasing to production
        </p>
      </div>
      <DeploymentSimulator />
    </div>
  );
}
