import { create } from 'zustand';

interface PermissionState {
  permissions: string[];
  isLoading: boolean;
  
  setPermissions: (perms: string[]) => void;
  setLoading: (loading: boolean) => void;
  hasPermission: (perm: string) => boolean;
  hasAnyPermission: (perms: string[]) => boolean;
  hasAllPermissions: (perms: string[]) => boolean;
  clear: () => void;
}

export const usePermissionStore = create<PermissionState>((set, get) => ({
  permissions: [],
  isLoading: false,
  
  setPermissions: (perms) => set({ permissions: perms }),
  setLoading: (loading) => set({ isLoading: loading }),
  
  hasPermission: (perm) => {
    const { permissions } = get();
    return permissions.includes('*') || permissions.includes(perm);
  },
  
  hasAnyPermission: (perms) => {
    const { permissions } = get();
    if (permissions.includes('*')) return true;
    return perms.some((p) => permissions.includes(p));
  },
  
  hasAllPermissions: (perms) => {
    const { permissions } = get();
    if (permissions.includes('*')) return true;
    return perms.every((p) => permissions.includes(p));
  },

  clear: () => set({ permissions: [] }),
}));
