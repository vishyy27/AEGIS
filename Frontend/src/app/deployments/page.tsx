"use client";

import React from "react";
import DeploymentTable from "@/components/DeploymentTable";
import { Filter, SlidersHorizontal, Download } from "lucide-react";

export default function Deployments() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <h1
            style={{
              fontSize: "1.75rem",
              fontWeight: 700,
              marginBottom: "8px",
            }}
          >
            Deployments
          </h1>
          <p style={{ color: "rgba(255, 255, 255, 0.4)", fontSize: "0.9rem" }}>
            Browse and filter historical deployment records and risk
            evaluations.
          </p>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <button
            className="glass"
            style={{
              padding: "10px 16px",
              color: "white",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              cursor: "pointer",
              fontSize: "0.85rem",
            }}
          >
            <Filter size={16} /> Filters
          </button>
          <button
            style={{
              background: "var(--primary)",
              border: "none",
              padding: "10px 16px",
              borderRadius: "10px",
              color: "white",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              cursor: "pointer",
              fontSize: "0.85rem",
              fontWeight: 600,
            }}
          >
            <Download size={16} /> Export CSV
          </button>
        </div>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "24px",
        }}
      >
        <div className="glass-card" style={{ padding: "16px" }}>
          <span
            style={{
              fontSize: "0.75rem",
              color: "rgba(255,255,255,0.4)",
              fontWeight: 600,
            }}
          >
            TOTAL DEPLOYMENTS
          </span>
          <div
            style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: "4px" }}
          >
            1,248
          </div>
        </div>
        <div className="glass-card" style={{ padding: "16px" }}>
          <span
            style={{
              fontSize: "0.75rem",
              color: "rgba(255,255,255,0.4)",
              fontWeight: 600,
            }}
          >
            AVG RISK SCORE
          </span>
          <div
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              marginTop: "4px",
              color: "var(--risk-low)",
            }}
          >
            18.2%
          </div>
        </div>
        <div className="glass-card" style={{ padding: "16px" }}>
          <span
            style={{
              fontSize: "0.75rem",
              color: "rgba(255,255,255,0.4)",
              fontWeight: 600,
            }}
          >
            FAILED RELEASES
          </span>
          <div
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              marginTop: "4px",
              color: "var(--risk-high)",
            }}
          >
            12
          </div>
        </div>
        <div className="glass-card" style={{ padding: "16px" }}>
          <span
            style={{
              fontSize: "0.75rem",
              color: "rgba(255,255,255,0.4)",
              fontWeight: 600,
            }}
          >
            ROLLBACKS
          </span>
          <div
            style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: "4px" }}
          >
            7
          </div>
        </div>
      </div>

      <DeploymentTable />
    </div>
  );
}
