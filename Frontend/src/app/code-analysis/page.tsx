"use client";

import React, { useState } from "react";
import {
  FileCode,
  Hash,
  BarChart3,
  History,
  Terminal,
  Play,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AnalysisResult {
  score: number;
  level: string;
  confidence: number;
  breakdown: Array<{ label: string; val: number }>;
}

export default function CodeAnalysis() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const [params, setParams] = useState({
    files_changed: 24,
    lines_added: 1240,
    complexity_score: 65,
    test_coverage: 82,
    historical_success: 94,
  });

  const startAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const resp = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      if (resp.ok) {
        const data = await resp.json();
        setResult({
          score: Math.round(data.risk_score),
          level: data.risk_level.toUpperCase(),
          confidence: Math.round(data.confidence),
          breakdown: [
            {
              label: "Complexity",
              val: Math.round(data.breakdown.complexity_weight),
            },
            {
              label: "Files Changed",
              val: Math.round(data.breakdown.files_changed_weight),
            },
            {
              label: "Coverage Penalty",
              val: Math.round(data.breakdown.test_coverage_penalty),
            },
          ],
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <header>
        <h1
          style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "8px" }}
        >
          Code Analysis
        </h1>
        <p style={{ color: "rgba(255, 255, 255, 0.4)", fontSize: "0.9rem" }}>
          Quantify the risk of individual deployment packages before release.
        </p>
      </header>

      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "32px" }}
      >
        {/* Input Panel */}
        <div
          className="glass-card"
          style={{ display: "flex", flexDirection: "column", gap: "24px" }}
        >
          <h2
            style={{
              fontSize: "1.1rem",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <FileCode size={20} color="var(--primary)" />
            Deployment Parameters
          </h2>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "20px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  color: "rgba(255, 255, 255, 0.4)",
                  marginBottom: "8px",
                }}
              >
                FILES CHANGED
              </label>
              <input
                type="number"
                value={params.files_changed}
                onChange={(e) =>
                  setParams({
                    ...params,
                    files_changed: Number(e.target.value),
                  })
                }
                className="glass"
                style={{
                  width: "100%",
                  border: "1px solid var(--glass-border)",
                  background: "rgba(255,255,255,0.02)",
                  padding: "12px",
                  color: "white",
                  borderRadius: "8px",
                  outline: "none",
                }}
              />
            </div>
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  color: "rgba(255, 255, 255, 0.4)",
                  marginBottom: "8px",
                }}
              >
                LINES ADDED
              </label>
              <input
                type="number"
                value={params.lines_added}
                onChange={(e) =>
                  setParams({ ...params, lines_added: Number(e.target.value) })
                }
                className="glass"
                style={{
                  width: "100%",
                  border: "1px solid var(--glass-border)",
                  background: "rgba(255,255,255,0.02)",
                  padding: "12px",
                  color: "white",
                  borderRadius: "8px",
                  outline: "none",
                }}
              />
            </div>
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.75rem",
                color: "rgba(255, 255, 255, 0.4)",
                marginBottom: "8px",
              }}
            >
              CODE COMPLEXITY SCORE (0-100)
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={params.complexity_score}
              onChange={(e) =>
                setParams({
                  ...params,
                  complexity_score: Number(e.target.value),
                })
              }
              style={{ width: "100%", accentColor: "var(--primary)" }}
            />
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "20px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  color: "rgba(255, 255, 255, 0.4)",
                  marginBottom: "8px",
                }}
              >
                TEST COVERAGE %
              </label>
              <input
                type="number"
                value={params.test_coverage}
                onChange={(e) =>
                  setParams({
                    ...params,
                    test_coverage: Number(e.target.value),
                  })
                }
                className="glass"
                style={{
                  width: "100%",
                  border: "1px solid var(--glass-border)",
                  background: "rgba(255,255,255,0.02)",
                  padding: "12px",
                  color: "white",
                  borderRadius: "8px",
                  outline: "none",
                }}
              />
            </div>
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  color: "rgba(255, 255, 255, 0.4)",
                  marginBottom: "8px",
                }}
              >
                HISTORICAL STABILITY
              </label>
              <input
                type="number"
                value={params.historical_success}
                onChange={(e) =>
                  setParams({
                    ...params,
                    historical_success: Number(e.target.value),
                  })
                }
                className="glass"
                style={{
                  width: "100%",
                  border: "1px solid var(--glass-border)",
                  background: "rgba(255,255,255,0.02)",
                  padding: "12px",
                  color: "white",
                  borderRadius: "8px",
                  outline: "none",
                }}
              />
            </div>
          </div>

          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={startAnalysis}
            disabled={isAnalyzing}
            style={{
              marginTop: "12px",
              padding: "16px",
              background: "var(--primary)",
              border: "none",
              borderRadius: "12px",
              color: "white",
              fontWeight: 700,
              fontSize: "1rem",
              cursor: isAnalyzing ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "12px",
              opacity: isAnalyzing ? 0.7 : 1,
            }}
          >
            {isAnalyzing ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1 }}
              >
                <History size={20} />
              </motion.div>
            ) : (
              <Play size={20} fill="white" />
            )}
            {isAnalyzing ? "Processing AI Model..." : "Analyze Deployment Risk"}
          </motion.button>
        </div>

        {/* Result Side */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <AnimatePresence mode="wait">
            {!result && !isAnalyzing && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                  flex: 1,
                  border: "2px dashed var(--glass-border)",
                  borderRadius: "20px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "16px",
                  color: "rgba(255,255,255,0.2)",
                }}
              >
                <Terminal size={48} />
                <span>Ready for analysis input</span>
              </motion.div>
            )}

            {isAnalyzing && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "24px",
                }}
              >
                <div
                  style={{
                    width: "64px",
                    height: "64px",
                    border: "4px solid var(--primary)",
                    borderTopColor: "transparent",
                    borderRadius: "50%",
                    animation: "spin 1s linear infinite",
                  }}
                />
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                <div style={{ textAlign: "center" }}>
                  <h3 style={{ fontWeight: 600, marginBottom: "8px" }}>
                    Evaluating Pattern History
                  </h3>
                  <p
                    style={{
                      fontSize: "0.85rem",
                      color: "rgba(255,255,255,0.4)",
                    }}
                  >
                    Checking similar deployment signatures from 14,321
                    releases...
                  </p>
                </div>
              </motion.div>
            )}

            {result && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "24px",
                }}
              >
                <div
                  className="glass-card"
                  style={{ border: "1px solid var(--risk-medium)" }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: "16px",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "0.85rem",
                        color: "rgba(255,255,255,0.5)",
                      }}
                    >
                      RISK LEVEL
                    </span>
                    <span
                      style={{
                        fontSize: "0.85rem",
                        fontWeight: 800,
                        color: "var(--risk-medium)",
                      }}
                    >
                      {result.level}
                    </span>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "baseline",
                      gap: "12px",
                    }}
                  >
                    <h2 style={{ fontSize: "3.5rem", fontWeight: 800 }}>
                      {result.score}
                    </h2>
                    <span
                      style={{
                        fontSize: "1rem",
                        color: "rgba(255,255,255,0.5)",
                      }}
                    >
                      / 100
                    </span>
                  </div>
                  <div
                    style={{
                      marginTop: "20px",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      color: "rgba(255,255,255,0.5)",
                      fontSize: "0.8rem",
                    }}
                  >
                    <CheckCircle2 size={14} color="var(--risk-low)" />
                    Confidence:{" "}
                    <span style={{ color: "white", fontWeight: 600 }}>
                      {result.confidence}%
                    </span>
                  </div>
                </div>

                <div className="glass-card">
                  <h3
                    style={{
                      fontSize: "0.9rem",
                      fontWeight: 600,
                      marginBottom: "20px",
                    }}
                  >
                    Risk Breakdown
                  </h3>
                  {result.breakdown.map(
                    (item: { label: string; val: number }) => (
                      <div key={item.label} style={{ marginBottom: "16px" }}>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            fontSize: "0.8rem",
                            marginBottom: "6px",
                          }}
                        >
                          <span>{item.label}</span>
                          <span>{item.val}%</span>
                        </div>
                        <div
                          style={{
                            height: "4px",
                            background: "rgba(255,255,255,0.05)",
                            borderRadius: "2px",
                          }}
                        >
                          <div
                            style={{
                              width: `${item.val}%`,
                              height: "100%",
                              background: "var(--primary)",
                            }}
                          />
                        </div>
                      </div>
                    ),
                  )}
                </div>

                <div
                  className="glass-card"
                  style={{
                    background: "rgba(239, 68, 68, 0.05)",
                    border: "1px solid rgba(239, 68, 68, 0.2)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      marginBottom: "12px",
                    }}
                  >
                    <AlertCircle size={18} color="var(--risk-high)" />
                    <h3 style={{ fontSize: "0.9rem", fontWeight: 600 }}>
                      Remediation Suggestions
                    </h3>
                  </div>
                  <ul
                    style={{
                      fontSize: "0.85rem",
                      color: "rgba(255,255,255,0.7)",
                      paddingLeft: "20px",
                      lineHeight: 2,
                    }}
                  >
                    <li>Reduce deployment batch size</li>
                    <li>Add integration tests for Auth module</li>
                    <li>Run performance validation on Staging</li>
                  </ul>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
