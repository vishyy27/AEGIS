"use client";

import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { getWSUrl } from "@/lib/api";

export interface WSMessage {
  type: string;
  [key: string]: unknown;
}

interface WebSocketContextType {
  messages: WSMessage[];
  lastMessage: WSMessage | null;
  connected: boolean;
  send: (data: Record<string, unknown>) => void;
  subscribe: (topics: string[]) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [activeTopics, setActiveTopics] = useState<Set<string>>(new Set(["telemetry", "alerts", "deployments", "policy"]));
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    try {
      const url = getWSUrl(Array.from(activeTopics));
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        reconnectAttemptsRef.current = 0;
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSMessage;
          setLastMessage(data);
          setMessages((prev) => {
            const next = [data, ...prev];
            return next.slice(0, 200); // Keep last 200 messages centrally
          });
        } catch { /* ignore parse errors */ }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        
        // Exponential backoff reconnect
        const delay = Math.min(10000, 1000 * Math.pow(1.5, reconnectAttemptsRef.current));
        reconnectAttemptsRef.current += 1;
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      ws.onerror = () => {
        // Just let onclose handle reconnect
        ws.close();
      };
    } catch { 
      // Handle edge cases
    }
  }, [activeTopics]);

  useEffect(() => {
    connect();
    
    // Check if we go back online
    const handleOnline = () => {
      // Use ref or just call connect, connect() checks readyState anyway
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
    
    // If topics changed, reconnect
    if (changed && wsRef.current) {
      wsRef.current.close(); // Triggers reconnect with new topics
    }
  }, []);

  return (
    <WebSocketContext.Provider value={{ messages, lastMessage, connected, send, subscribe }}>
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
