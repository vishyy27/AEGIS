"use client";

import React from "react";
import {
  TrendingUp,
  AlertTriangle,
  Target,
  Zap,
  BarChart,
  BarChart3,
} from "lucide-react";

export default function RiskInsights() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <header>
        <h1
          style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "8px" }}
        >
          Risk Insights
        </h1>
        <p style={{ color: "rgba(255, 255, 255, 0.4)", fontSize: "0.9rem" }}>
          Long-term AI analytics and pattern matching from historical data.
        </p>
      </header>

      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}
      >
        <div className="glass-card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "20px",
            }}
          >
            <TrendingUp size={20} color="var(--primary)" />
            <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>
              Failure Pattern Detection
            </h3>
          </div>
          <p
            style={{
              fontSize: "0.85rem",
              color: "rgba(255, 255, 255, 0.5)",
              marginBottom: "24px",
              lineHeight: 1.6,
            }}
          >
            AI has identified that failures mostly occur when:
          </p>
          <div
            style={{ display: "flex", flexDirection: "column", gap: "12px" }}
          >
            <div
              style={{
                background: "rgba(239, 68, 68, 0.05)",
                padding: "16px",
                borderRadius: "12px",
                border: "1px solid rgba(239, 68, 68, 0.2)",
              }}
            >
              <div
                style={{
                  fontWeight: 600,
                  fontSize: "0.9rem",
                  marginBottom: "4px",
                }}
              >
                Large Code Changes
              </div>
              <div
                style={{
                  fontSize: "0.8rem",
                  color: "rgba(255, 255, 255, 0.4)",
                }}
              >
                Lines of code (LOC) &gt; 1,200 per PR increases risk by 45%.
              </div>
            </div>
            <div
              style={{
                background: "rgba(245, 158, 11, 0.05)",
                padding: "16px",
                borderRadius: "12px",
                border: "1px solid rgba(245, 158, 11, 0.2)",
              }}
            >
              <div
                style={{
                  fontWeight: 600,
                  fontSize: "0.9rem",
                  marginBottom: "4px",
                }}
              >
                Complexity Spike
              </div>
              <div
                style={{
                  fontSize: "0.8rem",
                  color: "rgba(255, 255, 255, 0.4)",
                }}
              >
                Complexity score &gt; 75 on Auth module has 90% failure
                correlation.
              </div>
            </div>
          </div>
        </div>

        <div className="glass-card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "20px",
            }}
          >
            <Target size={20} color="var(--primary)" />
            <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>
              Service Risk Ranking
            </h3>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid var(--glass-border)",
                }}
              >
                <th
                  style={{
                    padding: "12px 0",
                    fontSize: "0.75rem",
                    color: "rgba(255,255,255,0.4)",
                  }}
                >
                  SERVICE
                </th>
                <th
                  style={{
                    padding: "12px 0",
                    fontSize: "0.75rem",
                    color: "rgba(255,255,255,0.4)",
                    textAlign: "center",
                  }}
                >
                  AVG RISK
                </th>
                <th
                  style={{
                    padding: "12px 0",
                    fontSize: "0.75rem",
                    color: "rgba(255,255,255,0.4)",
                    textAlign: "right",
                  }}
                >
                  TREND
                </th>
              </tr>
            </thead>
            <tbody>
              {[
                { name: "auth-service", risk: 72, trend: "up" },
                { name: "payment-gateway", risk: 45, trend: "down" },
                { name: "inventory-api", risk: 22, trend: "stable" },
                { name: "user-profile", risk: 18, trend: "stable" },
              ].map((s) => (
                <tr
                  key={s.name}
                  style={{ borderBottom: "1px solid rgba(255,255,255,0.02)" }}
                >
                  <td
                    style={{
                      padding: "16px 0",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                    }}
                  >
                    {s.name}
                  </td>
                  <td style={{ padding: "16px 0", textAlign: "center" }}>
                    <span
                      style={{
                        color:
                          s.risk > 60
                            ? "var(--risk-high)"
                            : s.risk > 30
                              ? "var(--risk-medium)"
                              : "var(--risk-low)",
                        fontWeight: 700,
                      }}
                    >
                      {s.risk}%
                    </span>
                  </td>
                  <td
                    style={{
                      padding: "16px 0",
                      textAlign: "right",
                      color: "rgba(255,255,255,0.4)",
                      fontSize: "0.8rem",
                    }}
                  >
                    {s.trend}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="glass-card">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            marginBottom: "24px",
          }}
        >
          <Zap size={20} color="var(--primary)" />
          <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>
            Model Prediction Accuracy
          </h3>
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "20px",
          }}
        >
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: 800 }}>96.4%</div>
            <div
              style={{
                fontSize: "0.75rem",
                color: "rgba(255,255,255,0.4)",
                marginTop: "4px",
              }}
            >
              MODEl ACCURACY
            </div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                fontSize: "2rem",
                fontWeight: 800,
                color: "var(--risk-medium)",
              }}
            >
              2.1%
            </div>
            <div
              style={{
                fontSize: "0.75rem",
                color: "rgba(255,255,255,0.4)",
                marginTop: "4px",
              }}
            >
              FALSE POSITIVES
            </div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                fontSize: "2rem",
                fontWeight: 800,
                color: "var(--risk-high)",
              }}
            >
              1.5%
            </div>
            <div
              style={{
                fontSize: "0.75rem",
                color: "rgba(255,255,255,0.4)",
                marginTop: "4px",
              }}
            >
              FALSE NEGATIVES
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
