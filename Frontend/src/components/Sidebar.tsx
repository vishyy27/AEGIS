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
  { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
  { label: "Code Analysis", icon: Code2, href: "/code-analysis" },
  { label: "Deployments", icon: Rocket, href: "/deployments" },
  { label: "Risk Insights", icon: Activity, href: "/risk-insights" },
  { label: "Integrations", icon: Layers, href: "/integrations" },
  { label: "Settings", icon: Settings, href: "/settings" },
];

const intelligence = [
  { label: "AI Assistant", icon: Sparkles, href: "/ai-assistant" },
  { label: "Simulation Lab", icon: FlaskConical, href: "/simulation-lab" },
  { label: "Deployment Replay", icon: Clock, href: "/deployment-replay" },
  { label: "Incident Center", icon: AlertOctagon, href: "/incident-center" },
  { label: "Fleet Intelligence", icon: Network, href: "/fleet-intelligence" },
];

function NavLink({ item, active }: { item: typeof nav[0]; active: boolean }) {
  return (
    <Link href={item.href} className="outline-none">
      <div className={cn(
        "flex items-center gap-2.5 px-3 py-[7px] rounded-md text-[13px] transition-colors duration-150",
        active
          ? "bg-white/[0.06] text-white font-medium"
          : "text-[#6b7280] hover:text-[#9ca3af] hover:bg-white/[0.03]",
      )}>
        <item.icon size={16} strokeWidth={active ? 2 : 1.5} className={active ? "text-blue-400" : "text-[#4b5563]"} />
        {item.label}
      </div>
    </Link>
  );
}

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-[220px] h-screen fixed left-0 top-0 bg-[#0a0e1a] border-r border-[#1c2333] flex flex-col z-50">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-14 border-b border-[#1c2333]">
        <ShieldCheck size={20} className="text-blue-400" />
        <span className="text-[15px] font-semibold tracking-tight text-white">AEGIS</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-0.5">
        {nav.map(item => (
          <NavLink key={item.href} item={item} active={pathname === item.href} />
        ))}

        <div className="flex items-center gap-2 px-3 pt-5 pb-2">
          <span className="text-[10px] font-medium text-[#3d4454] uppercase tracking-[0.08em]">Intelligence</span>
          <div className="h-px flex-1 bg-[#1c2333]" />
        </div>

        {intelligence.map(item => (
          <NavLink key={item.href} item={item} active={pathname === item.href} />
        ))}
      </nav>

      <div className="px-5 py-3 border-t border-[#1c2333]">
        <span className="text-[10px] text-[#3d4454] font-medium">AEGIS v2.0</span>
      </div>
    </aside>
  );
}
