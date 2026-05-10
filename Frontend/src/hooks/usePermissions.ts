import { usePermissionStore } from '@/store/permissionStore';

export function usePermissions() {
  const hasPermission = usePermissionStore(state => state.hasPermission);
  const hasAnyPermission = usePermissionStore(state => state.hasAnyPermission);
  const hasAllPermissions = usePermissionStore(state => state.hasAllPermissions);
  const isLoading = usePermissionStore(state => state.isLoading);

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isLoading
  };
}
