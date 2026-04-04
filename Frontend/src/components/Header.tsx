"use client";

import React from "react";
import { Search, Bell, User, ChevronDown, Globe } from "lucide-react";

export default function Header() {
  return (
    <header className="h-16 fixed top-0 left-[240px] right-0 bg-[#020617]/80 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-8 z-40">
      <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 w-96 gap-3">
        <Search size={18} className="text-slate-500" />
        <input
          type="text"
          placeholder="Search deployments, services..."
          className="bg-transparent border-none text-white text-sm outline-none w-full placeholder:text-slate-600"
        />
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 bg-cyan-500/10 border border-cyan-500/20 px-3 py-1 rounded-full cursor-pointer hover:bg-cyan-500/20 transition-colors">
          <Globe size={14} className="text-cyan-500" />
          <span className="text-xs font-semibold text-cyan-500">
            Production
          </span>
          <ChevronDown size={14} className="text-cyan-500" />
        </div>

        <div className="flex items-center gap-4">
          <button className="text-slate-400 hover:text-white transition-colors relative">
            <Bell size={20} />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full border-2 border-[#020617]" />
          </button>

          <div className="flex items-center gap-2 group cursor-pointer border-l border-slate-800 pl-4">
            <div className="w-8 h-8 rounded-lg bg-cyan-600 flex items-center justify-center text-white ring-2 ring-transparent group-hover:ring-cyan-500/50 transition-all">
              <User size={18} />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
