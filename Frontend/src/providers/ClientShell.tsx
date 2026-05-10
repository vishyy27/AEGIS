"use client";

import React from "react";
import ErrorBoundary from "@/components/system/ErrorBoundary";
import ConnectionOverlay from "@/components/system/ConnectionOverlay";

export default function ClientShell({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary fallbackTitle="Application Error">
      {children}
      <ConnectionOverlay />
    </ErrorBoundary>
  );
}
