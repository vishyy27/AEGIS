"use client";

import React from "react";
import { FlaskConical } from "lucide-react";
import DeploymentSimulator from "@/components/DeploymentSimulator";

export default function SimulationLabPage() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">Simulation Lab</h1>
        <p className="text-muted mt-0.5">Test synthetic deployments against real ML + Policy engines before release</p>
      </div>
      <DeploymentSimulator />
    </div>
  );
}
