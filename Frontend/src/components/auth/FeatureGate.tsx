"use client";

import React, { ReactNode } from 'react';
import { usePermissions } from '@/hooks/usePermissions';

interface FeatureGateProps {
  permission?: string;
  anyPermission?: string[];
  allPermissions?: string[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function FeatureGate({
  permission,
  anyPermission,
  allPermissions,
  children,
  fallback = null
}: FeatureGateProps) {
  const { hasPermission, hasAnyPermission, hasAllPermissions, isLoading } = usePermissions();

  if (isLoading) return null; // Or a skeleton/spinner

  let isAllowed = false;

  if (permission && hasPermission(permission)) {
    isAllowed = true;
  } else if (anyPermission && hasAnyPermission(anyPermission)) {
    isAllowed = true;
  } else if (allPermissions && hasAllPermissions(allPermissions)) {
    isAllowed = true;
  }

  // If no conditions provided, default to false
  if (!permission && !anyPermission && !allPermissions) {
    isAllowed = false;
  }

  return <>{isAllowed ? children : fallback}</>;
}
