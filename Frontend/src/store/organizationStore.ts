import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  role: string;
}

interface OrganizationState {
  currentOrg: Organization | null;
  organizations: Organization[];
  isLoading: boolean;
  
  setCurrentOrg: (org: Organization | null) => void;
  setOrganizations: (orgs: Organization[]) => void;
  setLoading: (loading: boolean) => void;
}

export const useOrganizationStore = create<OrganizationState>()(
  persist(
    (set) => ({
      currentOrg: null,
      organizations: [],
      isLoading: false,
      
      setCurrentOrg: (org) => set({ currentOrg: org }),
      setOrganizations: (orgs) => set({ organizations: orgs }),
      setLoading: (loading) => set({ isLoading: loading }),
    }),
    {
      name: 'aegis-org-storage',
      partialize: (state) => ({ currentOrg: state.currentOrg }),
    }
  )
);
