import React, { useEffect } from 'react';
import { useOrganizationStore, Organization } from '@/store/organizationStore';
import { usePermissionStore } from '@/store/permissionStore';
import { fetchAPI } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';

export function OrganizationProvider({ children }: { children: React.ReactNode }) {
  const { currentOrg, setCurrentOrg, setOrganizations, setLoading } = useOrganizationStore();
  const { setPermissions, setLoading: setPermLoading, clear: clearPerms } = usePermissionStore();

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
  }, [setOrganizations, setLoading, setCurrentOrg]);

  // When org changes:
  // 1. Fetch permissions for new org
  // 2. Clear query cache to prevent cross-tenant data visible in UI
  useEffect(() => {
    async function syncPermissions() {
      if (!currentOrg) {
        clearPerms();
        return;
      }
      
      setPermLoading(true);
      try {
        const perms = await fetchAPI<string[]>(`/api/organizations/${currentOrg.id}/permissions/me`);
        setPermissions(perms);
      } catch (e) {
        console.error('[OrganizationProvider] Failed to fetch permissions', e);
        clearPerms();
      } finally {
        setPermLoading(false);
      }
    }

    queryClient.clear();
    syncPermissions();
  }, [currentOrg?.id, setPermissions, setPermLoading, clearPerms]);

  return <>{children}</>;
}
