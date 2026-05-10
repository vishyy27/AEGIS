"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";

// ---- Deployment Hooks ----

interface Deployment {
  id: number;
  repo_name: string;
  environment: string;
  risk_score: number;
  decision: string;
  outcome: string;
  timestamp: string;
}

export function useDeployments(limit = 10) {
  return useQuery({
    queryKey: ["deployments", limit],
    queryFn: () => fetchAPI<Deployment[]>(`/api/deployments/?limit=${limit}`),
    staleTime: 10000,
  });
}

export function useDeploymentById(id: number) {
  return useQuery({
    queryKey: ["deployment", id],
    queryFn: () => fetchAPI<Deployment>(`/api/deployments/${id}`),
    enabled: !!id,
  });
}

// ---- Dashboard Hooks ----

interface DashboardSummary {
  globalRiskScore: number;
  incidentFrequency: number;
  successRate: number;
  riskTrend: number[];
  topRiskFactors: { factor: string; impact: string }[];
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => fetchAPI<DashboardSummary>("/api/dashboard/summary"),
    staleTime: 15000,
  });
}

// ---- Incident Hooks ----

export function useIncidents(limit = 20) {
  return useQuery({
    queryKey: ["incidents", limit],
    queryFn: () => fetchAPI<any[]>(`/api/incidents/?limit=${limit}`),
    staleTime: 10000,
  });
}

// ---- Telemetry / Events Hooks ----

export function useTelemetryEvents(limit = 50) {
  return useQuery({
    queryKey: ["telemetry", "events", limit],
    queryFn: () => fetchAPI<any[]>(`/api/telemetry/events?limit=${limit}`),
    staleTime: 5000,
  });
}

// ---- Anomaly Hooks ----

export function useAnomalies(limit = 20) {
  return useQuery({
    queryKey: ["anomalies", limit],
    queryFn: () => fetchAPI<any[]>(`/api/telemetry/events?event_type=anomaly_event&limit=${limit}`),
    staleTime: 10000,
  });
}

// ---- Replay Hooks ----

export function useDeploymentReplay(deploymentId: number) {
  return useQuery({
    queryKey: ["replay", deploymentId],
    queryFn: () => fetchAPI<any>(`/api/replay/deployment/${deploymentId}/timeline`),
    enabled: !!deploymentId,
    staleTime: 60000,
  });
}

// ---- Health Hook ----

export function useApiHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => fetchAPI<{ status: string; database: string; ml_model: string }>("/health"),
    refetchInterval: 30000,
    staleTime: 10000,
  });
}

// ---- Fleet Intelligence ----

export function useFleetStatus() {
  return useQuery({
    queryKey: ["fleet", "status"],
    queryFn: () => fetchAPI<any>("/api/fleet/status"),
    staleTime: 10000,
  });
}
