"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Code2,
  Rocket,
  Activity,
  Layers,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const menuItems = [
  { name: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
  { name: "Code Analysis", icon: Code2, href: "/code-analysis" },
  { name: "Deployments", icon: Rocket, href: "/deployments" },
  { name: "Risk Insights", icon: Activity, href: "/risk-insights" },
  { name: "Integrations", icon: Layers, href: "/integrations" },
  { name: "Settings", icon: Settings, href: "/settings" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-[240px] h-screen fixed left-0 top-0 bg-[#020617] border-r border-slate-800 flex flex-col p-4 z-50">
      <div className="flex items-center gap-3 px-3 py-6 text-cyan-500 font-bold text-xl mb-4">
        <ShieldCheck size={32} />
        <span className="tracking-tight">AEGIS</span>
      </div>

      <nav className="flex-1 flex flex-col gap-1">
        {menuItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className="group outline-none"
            >
              <div
                className={cn(
                  "relative flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 cursor-pointer",
                  isActive
                    ? "bg-slate-800/40 text-cyan-400 font-medium"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/20",
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 w-1.5 h-6 bg-cyan-500 rounded-full"
                  />
                )}
                <item.icon
                  size={20}
                  className={
                    isActive
                      ? "text-cyan-400"
                      : "text-slate-500 group-hover:text-slate-300"
                  }
                />
                <span className="text-sm">{item.name}</span>
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="px-3 py-4 text-[10px] text-slate-600 font-medium uppercase tracking-widest border-t border-slate-800/50">
        v1.0.2 Stable
      </div>
    </aside>
  );
}
