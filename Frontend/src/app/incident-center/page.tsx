"use client";

import React from "react";
import IncidentGraph from "@/components/IncidentGraph";

export default function IncidentCenterPage() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">Incident Center</h1>
        <p className="text-muted mt-0.5">Correlated incident timelines and failure chain analysis</p>
      </div>
      <IncidentGraph />
    </div>
  );
}
