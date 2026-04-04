"use client";

import React from "react";
import {
  Github,
  Linkedin,
  Cloud,
  Box,
  Terminal,
  Ship,
  CheckCircle2,
  Plus,
} from "lucide-react";
import { motion } from "framer-motion";

const integrations = [
  {
    name: "GitHub",
    icon: Github,
    status: "Connected",
    description: "Auto-sync PRs and commit history for risk analysis.",
  },
  {
    name: "GitLab",
    icon: Terminal,
    status: "Not Connected",
    description: "Connect GitLab CI/CD pipelines and webhooks.",
  },
  {
    name: "Jenkins",
    icon: Ship,
    status: "Not Connected",
    description: "Monitor Jenkins build jobs and deployment logs.",
  },
  {
    name: "AWS Cloud",
    icon: Cloud,
    status: "Connected",
    description: "Track production environment health and resource usage.",
  },
  {
    name: "Azure DevOps",
    icon: Box,
    status: "Not Connected",
    description: "Integrate with Azure release pipelines and boards.",
  },
  {
    name: "Kubernetes",
    icon: Ship,
    status: "Connected",
    description: "Real-time observation of K8s clusters and pods.",
  },
];

export default function Integrations() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <header>
        <h1
          style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "8px" }}
        >
          Integrations
        </h1>
        <p style={{ color: "rgba(255, 255, 255, 0.4)", fontSize: "0.9rem" }}>
          Connect your CI/CD stack to enable deep AI risk analysis.
        </p>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
          gap: "24px",
        }}
      >
        {integrations.map((item, i) => (
          <motion.div
            key={item.name}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.05 }}
            className="glass-card"
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "16px",
              justifyContent: "space-between",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
              }}
            >
              <div
                style={{
                  padding: "12px",
                  background: "var(--glass)",
                  borderRadius: "12px",
                  border: "1px solid var(--glass-border)",
                }}
              >
                <item.icon
                  size={24}
                  color={
                    item.status === "Connected"
                      ? "var(--primary)"
                      : "rgba(255,255,255,0.4)"
                  }
                />
              </div>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 700,
                  padding: "4px 8px",
                  borderRadius: "6px",
                  background:
                    item.status === "Connected"
                      ? "rgba(16, 185, 129, 0.1)"
                      : "rgba(255,255,255,0.05)",
                  color:
                    item.status === "Connected"
                      ? "var(--risk-low)"
                      : "rgba(255,255,255,0.4)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                {item.status === "Connected" && <CheckCircle2 size={10} />}
                {item.status.toUpperCase()}
              </span>
            </div>

            <div>
              <h3
                style={{
                  fontSize: "1.1rem",
                  fontWeight: 700,
                  marginBottom: "8px",
                }}
              >
                {item.name}
              </h3>
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "rgba(255,255,255,0.5)",
                  lineHeight: 1.5,
                }}
              >
                {item.description}
              </p>
            </div>

            <button
              style={{
                width: "100%",
                padding: "12px",
                borderRadius: "10px",
                background:
                  item.status === "Connected"
                    ? "transparent"
                    : "var(--primary)",
                border:
                  item.status === "Connected"
                    ? "1px solid var(--glass-border)"
                    : "none",
                color: "white",
                fontSize: "0.85rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
              }}
            >
              {item.status === "Connected" ? (
                "Manage"
              ) : (
                <>
                  <Plus size={16} /> Connect
                </>
              )}
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
