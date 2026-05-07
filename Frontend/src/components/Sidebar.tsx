"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Code2, Rocket, Activity, Layers, Settings,
  ShieldCheck, Sparkles, FlaskConical, Clock, AlertOctagon, Network,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { label: "Mission Control", icon: LayoutDashboard, href: "/dashboard" },
  { label: "Code Analysis", icon: Code2, href: "/code-analysis" },
  { label: "Deployments", icon: Rocket, href: "/deployments" },
  { label: "Risk Insights", icon: Activity, href: "/risk-insights" },
  { label: "Integrations", icon: Layers, href: "/integrations" },
];

const intelligence = [
  { label: "AI Copilot", icon: Sparkles, href: "/ai-assistant" },
  { label: "Simulation Lab", icon: FlaskConical, href: "/simulation-lab" },
  { label: "Deployment Replay", icon: Clock, href: "/deployment-replay" },
  { label: "Incident War Room", icon: AlertOctagon, href: "/incident-center" },
  { label: "Fleet Intelligence", icon: Network, href: "/fleet-intelligence" },
];

function NavLink({ item, active }: { item: typeof nav[0]; active: boolean }) {
  return (
    <Link href={item.href} className="outline-none block group">
      <div className={cn(
        "flex items-center gap-2.5 px-3 py-2 rounded-md text-[13px] transition-all duration-200 relative overflow-hidden",
        active
          ? "bg-[#151a2e] text-white font-medium border border-[#232b3e] shadow-[inset_0_1px_2px_rgba(0,0,0,0.5)]"
          : "text-[#6b7280] hover:text-[#e2e8f0] hover:bg-[#151a2e]/50 border border-transparent",
      )}>
        {active && (
          <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
        )}
        <item.icon 
          size={16} 
          strokeWidth={active ? 2 : 1.5} 
          className={cn(
            "transition-colors duration-200", 
            active ? "text-blue-400" : "text-[#4b5563] group-hover:text-[#8892a8]"
          )} 
        />
        <span className="relative z-10">{item.label}</span>
      </div>
    </Link>
  );
}

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-[220px] h-screen fixed left-0 top-0 bg-[#0a0e1a] border-r border-[#1c2333] flex flex-col z-50">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-14 border-b border-[#1c2333] shrink-0 bg-[#0a0e1a] relative">
        <div className="relative">
          <ShieldCheck size={20} className="text-blue-500 relative z-10" />
          <div className="absolute inset-0 bg-blue-500/20 blur-md rounded-full" />
        </div>
        <span className="text-[15px] font-bold tracking-tight text-white flex items-center gap-1.5">
          AEGIS
          <span className="text-[8px] bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded border border-blue-500/20 leading-none h-fit">OS</span>
        </span>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1 scrollbar-hide">
        <div className="text-[9px] font-semibold text-[#4a5468] uppercase tracking-[0.1em] px-3 mb-2">Operations</div>
        {nav.map(item => (
          <NavLink key={item.href} item={item} active={pathname === item.href} />
        ))}

        <div className="pt-6 pb-2">
          <div className="flex items-center gap-2 px-3">
            <span className="text-[9px] font-semibold text-[#4a5468] uppercase tracking-[0.1em]">Intelligence</span>
            <div className="h-px flex-1 bg-gradient-to-r from-[#1c2333] to-transparent" />
          </div>
        </div>

        {intelligence.map(item => (
          <NavLink key={item.href} item={item} active={pathname === item.href} />
        ))}
      </nav>

      <div className="p-3 border-t border-[#1c2333] shrink-0">
        <Link href="/settings" className="block outline-none group">
          <div className={cn(
            "flex items-center gap-2.5 px-3 py-2 rounded-md text-[13px] transition-all duration-200",
            pathname === "/settings"
              ? "bg-[#151a2e] text-white font-medium border border-[#232b3e]"
              : "text-[#6b7280] hover:text-[#e2e8f0] hover:bg-[#151a2e]/50 border border-transparent"
          )}>
            <Settings size={16} className={pathname === "/settings" ? "text-[#8892a8]" : "text-[#4b5563] group-hover:text-[#8892a8]"} />
            Settings
          </div>
        </Link>
      </div>
    </aside>
  );
}
