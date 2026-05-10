"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[AEGIS ErrorBoundary]", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="aegis-card flex flex-col items-center justify-center py-12 text-center">
          <div className="w-12 h-12 rounded-full bg-rose-500/10 flex items-center justify-center mb-4">
            <AlertTriangle size={22} className="text-rose-400" />
          </div>
          <h3 className="text-[14px] font-semibold text-[#e2e8f0] mb-1">
            {this.props.fallbackTitle || "Component Error"}
          </h3>
          <p className="text-[12px] text-[#4a5468] mb-4 max-w-[300px]">
            {this.state.error?.message || "An unexpected error occurred in this section."}
          </p>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#151a2e] border border-[#1c2333] rounded-md text-[12px] text-[#8892a8] hover:text-white hover:border-[#3d4454] transition-colors"
          >
            <RefreshCw size={12} />
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
