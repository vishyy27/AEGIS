import { create } from 'zustand';

export interface TelemetryMetric {
  service: string;
  cpu: number;
  memory: number;
  latency: number;
  errors: number;
  timestamp: string;
}

interface TelemetryState {
  metrics: Record<string, TelemetryMetric>;
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting';
  lastUpdated: number;
  recentMessages: any[];
  
  updateMetric: (service: string, data: Partial<TelemetryMetric>) => void;
  setConnectionStatus: (status: 'connected' | 'disconnected' | 'reconnecting') => void;
  batchUpdate: (updates: Record<string, TelemetryMetric>) => void;
  addMessage: (msg: any) => void;
}

export const useTelemetryStore = create<TelemetryState>((set) => ({
  metrics: {},
  recentMessages: [],
  connectionStatus: 'disconnected',
  lastUpdated: Date.now(),
  
  updateMetric: (service, data) => set((state) => ({
    metrics: {
      ...state.metrics,
      [service]: {
        ...(state.metrics[service] || { service, cpu: 0, memory: 0, latency: 0, errors: 0, timestamp: new Date().toISOString() }),
        ...data,
      }
    },
    lastUpdated: Date.now()
  })),

  batchUpdate: (updates) => set((state) => ({
    metrics: {
      ...state.metrics,
      ...updates
    },
    lastUpdated: Date.now()
  })),

  addMessage: (msg: any) => set((state) => ({
    recentMessages: [msg, ...state.recentMessages].slice(0, 200)
  })),

  setConnectionStatus: (status) => set({ connectionStatus: status })
}));
