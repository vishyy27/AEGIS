"use client";

import React from "react";
import { AlertOctagon } from "lucide-react";
import IncidentGraph from "@/components/IncidentGraph";

export default function IncidentCenterPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title text-gradient-cyan flex items-center gap-3">
          <AlertOctagon size={28} className="text-red-400" />
          Incident Center
        </h1>
        <p className="text-muted mt-1">Correlated incident timelines and failure chain analysis</p>
      </div>
      <IncidentGraph />
    </div>
  );
}
