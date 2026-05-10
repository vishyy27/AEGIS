"use client";

import React, { useEffect } from 'react';
import { useOrganizationStore, Organization } from '@/store/organizationStore';
import { fetchAPI } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';

export function OrganizationProvider({ children }: { children: React.ReactNode }) {
  const { currentOrg, setCurrentOrg, setOrganizations, setLoading } = useOrganizationStore();

  useEffect(() => {
    async function loadOrganizations() {
      setLoading(true);
      try {
        const orgs = await fetchAPI<Organization[]>('/api/organizations/');
        setOrganizations(orgs);
        
        // If no current org, or current org no longer in list, pick the first one
        if (orgs.length > 0) {
          const stillExists = currentOrg && orgs.find(o => o.id === currentOrg.id);
          if (!stillExists) {
            setCurrentOrg(orgs[0]);
          }
        }
      } catch (error) {
        console.error('[OrganizationProvider] Failed to load organizations:', error);
      } finally {
        setLoading(false);
      }
    }

    loadOrganizations();
  }, [setOrganizations, setLoading, setCurrentOrg]); // Intentionally exclude currentOrg to avoid loop

  // When org changes, clear query cache to prevent cross-tenant data visible in UI
  useEffect(() => {
    if (currentOrg) {
      queryClient.clear();
    }
  }, [currentOrg?.id]);

  return <>{children}</>;
}
