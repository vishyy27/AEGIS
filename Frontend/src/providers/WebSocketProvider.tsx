"use client";

import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { getWSUrl } from "@/lib/api";
import { useTelemetryStore } from "@/store/telemetryStore";
import { useOperationalStore, DeploymentEvent } from "@/store/operationalStore";
import { queryClient } from "@/lib/queryClient";
import { streamValidator } from "@/lib/realtime/streamValidator";
import { reconciliationEngine } from "@/lib/realtime/reconciliationEngine";

export interface WSMessage {
  type: string;
  [key: string]: unknown;
}

interface WebSocketContextType {
  connected: boolean;
  send: (data: Record<string, unknown>) => void;
  subscribe: (topics: string[]) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [connected, setConnected] = useState(false);
  const [activeTopics, setActiveTopics] = useState<Set<string>>(new Set(["telemetry", "alerts", "deployments", "policy"]));
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  
  const updateMetric = useTelemetryStore(state => state.updateMetric);
  const batchUpdate = useTelemetryStore(state => state.batchUpdate);
  const setConnectionStatus = useTelemetryStore(state => state.setConnectionStatus);
  const upsertDeployment = useOperationalStore(state => state.upsertDeployment);
  const addAnomaly = useOperationalStore(state => state.addAnomaly);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    try {
      const url = getWSUrl(Array.from(activeTopics));
      const ws = new WebSocket(url);
      wsRef.current = ws;
      setConnectionStatus('reconnecting');

      ws.onopen = () => {
        setConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSMessage;
          if (!streamValidator.validate(data)) return;
          
          // Generate a synthetic ID if absent for deduplication
          const eventId = data.id || `${data.type}-${data.timestamp || Date.now()}-${Math.random()}`;
          if (reconciliationEngine.isDuplicate(eventId as string)) return;

          useTelemetryStore.getState().addMessage(data);
          
          switch (data.type) {
            case "telemetry":
              if (data.service && typeof data.service === 'string') {
                updateMetric(data.service, data as any);
              }
              break;
            case "telemetry_batch":
              if (data.updates && typeof data.updates === 'object') {
                batchUpdate(data.updates as any);
              }
              break;
            case "deployment_update":
              if (data.deployment) {
                upsertDeployment(data.deployment as DeploymentEvent);
                queryClient.invalidateQueries({ queryKey: ['deployments'] });
              }
              break;
            case "anomaly_detected":
              addAnomaly(data);
              queryClient.invalidateQueries({ queryKey: ['anomalies'] });
              break;
            case "policy_violation":
              queryClient.invalidateQueries({ queryKey: ['incidents'] });
              break;
          }
        } catch { /* ignore parse errors */ }
      };

      ws.onclose = () => {
        setConnected(false);
        setConnectionStatus('disconnected');
        wsRef.current = null;
        
        // Exponential backoff reconnect
        const delay = Math.min(10000, 1000 * Math.pow(1.5, reconnectAttemptsRef.current));
        reconnectAttemptsRef.current += 1;
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch { 
      // Handle edge cases
    }
  }, [activeTopics, updateMetric, batchUpdate, setConnectionStatus, upsertDeployment, addAnomaly]);

  useEffect(() => {
    connect();
    
    const handleOnline = () => {
      connect();
    };
    window.addEventListener("online", handleOnline);

    return () => {
      window.removeEventListener("online", handleOnline);
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const subscribe = useCallback((topics: string[]) => {
    let changed = false;
    setActiveTopics(prev => {
      const next = new Set(prev);
      topics.forEach(t => {
        if (!next.has(t)) {
          next.add(t);
          changed = true;
        }
      });
      return changed ? next : prev;
    });
    
    if (changed && wsRef.current) {
      wsRef.current.close(); 
    }
  }, []);

  return (
    <WebSocketContext.Provider value={{ connected, send, subscribe }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useGlobalWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useGlobalWebSocket must be used within a WebSocketProvider");
  }
  return context;
}
