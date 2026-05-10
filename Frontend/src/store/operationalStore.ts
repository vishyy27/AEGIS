import { create } from 'zustand';

export interface DeploymentEvent {
  id: string;
  service: string;
  version: string;
  environment: string;
  status: 'pending' | 'deploying' | 'healthy' | 'rollback' | 'failed';
  riskScore: number;
  timestamp: string;
}

interface OperationalState {
  activeDeployments: Record<string, DeploymentEvent>;
  recentAnomalies: any[];
  
  upsertDeployment: (dep: DeploymentEvent) => void;
  removeDeployment: (id: string) => void;
  addAnomaly: (anomaly: any) => void;
}

export const useOperationalStore = create<OperationalState>((set) => ({
  activeDeployments: {},
  recentAnomalies: [],
  
  upsertDeployment: (dep) => set((state) => ({
    activeDeployments: {
      ...state.activeDeployments,
      [dep.id]: dep
    }
  })),
  
  removeDeployment: (id) => set((state) => {
    const next = { ...state.activeDeployments };
    delete next[id];
    return { activeDeployments: next };
  }),

  addAnomaly: (anomaly) => set((state) => ({
    recentAnomalies: [anomaly, ...state.recentAnomalies].slice(0, 50)
  }))
}));
