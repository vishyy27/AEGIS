"use client";

import React from "react";
import {
  User,
  Lock,
  Bell,
  Database,
  Cpu,
  ShieldCheck,
  Save,
} from "lucide-react";

const SettingSection = ({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
}) => (
  <div
    className="glass-card"
    style={{ display: "flex", flexDirection: "column", gap: "20px" }}
  >
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "10px",
        color: "var(--primary)",
      }}
    >
      <Icon size={20} />
      <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "white" }}>
        {title}
      </h3>
    </div>
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {children}
    </div>
  </div>
);

const InputGroup = ({
  label,
  description,
  type = "text",
  defaultValue,
}: {
  label: string;
  description?: string;
  type?: string;
  defaultValue: string | number;
}) => (
  <div>
    <label
      style={{
        display: "block",
        fontSize: "0.8rem",
        fontWeight: 600,
        marginBottom: "4px",
      }}
    >
      {label}
    </label>
    {description && (
      <p
        style={{
          fontSize: "0.75rem",
          color: "rgba(255,255,255,0.4)",
          marginBottom: "8px",
        }}
      >
        {description}
      </p>
    )}
    <input
      type={type}
      defaultValue={defaultValue}
      style={{
        width: "100%",
        background: "rgba(255,255,255,0.02)",
        border: "1px solid var(--glass-border)",
        borderRadius: "8px",
        padding: "12px",
        color: "white",
        outline: "none",
        fontSize: "0.9rem",
      }}
    />
  </div>
);

export default function Settings() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "32px",
        maxWidth: "1000px",
      }}
    >
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
            Settings
          </h1>
          <p style={{ color: "rgba(255, 255, 255, 0.4)", fontSize: "0.9rem" }}>
            Configure your account, environment thresholds, and AI model
            sensitivity.
          </p>
        </div>
        <button
          style={{
            background: "var(--primary)",
            color: "white",
            border: "none",
            padding: "12px 24px",
            borderRadius: "10px",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <Save size={18} /> Save Changes
        </button>
      </header>

      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "32px" }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
          <SettingSection title="User Profile" icon={User}>
            <InputGroup label="Full Name" defaultValue="Admin User" />
            <InputGroup
              label="Email Address"
              defaultValue="admin@riskguard.ai"
              type="email"
            />
            <InputGroup label="Team Name" defaultValue="Release Management" />
          </SettingSection>

          <SettingSection title="Environment Config" icon={Database}>
            <InputGroup
              label="Production Cluster"
              defaultValue="k8s-prod-us-east"
            />
            <InputGroup
              label="Staging Cluster"
              defaultValue="k8s-staging-main"
            />
            <InputGroup
              label="Monitoring Endpoint"
              defaultValue="https://prometheus.riskguard.internal"
            />
          </SettingSection>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
          <SettingSection title="Model Settings" icon={Cpu}>
            <InputGroup
              label="Risk Threshold"
              description="Deployments with risk scores above this value will require manual approval."
              type="number"
              defaultValue={70}
            />
            <InputGroup
              label="Confidence Threshold"
              description="Minimum confidence score required for AI recommendations."
              type="number"
              defaultValue={85}
            />
          </SettingSection>

          <SettingSection title="Alert Triggers" icon={Bell}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span style={{ fontSize: "0.9rem" }}>
                Critical Risk Notification
              </span>
              <input
                type="checkbox"
                defaultChecked
                style={{ width: "40px", height: "20px" }}
              />
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span style={{ fontSize: "0.9rem" }}>
                Successful Deployment Summary
              </span>
              <input
                type="checkbox"
                style={{ width: "40px", height: "20px" }}
              />
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span style={{ fontSize: "0.9rem" }}>
                Model Recalibration Alerts
              </span>
              <input
                type="checkbox"
                defaultChecked
                style={{ width: "40px", height: "20px" }}
              />
            </div>
          </SettingSection>
        </div>
      </div>
    </div>
  );
}
