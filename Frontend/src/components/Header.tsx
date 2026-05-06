"use client";

import React from "react";
import { Search, Bell, User, ChevronDown, Circle } from "lucide-react";

export default function Header() {
  return (
    <header className="h-14 fixed top-0 left-[220px] right-0 bg-[#0a0e1a]/90 backdrop-blur-sm border-b border-[#1c2333] flex items-center justify-between px-6 z-40">
      <div className="flex items-center bg-[#0f1422] border border-[#1c2333] rounded-md px-3 py-1.5 w-80 gap-2">
        <Search size={14} className="text-[#4b5563]" />
        <input
          type="text"
          placeholder="Search deployments, services..."
          className="bg-transparent border-none text-[13px] text-white outline-none w-full placeholder:text-[#3d4454]"
        />
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5 text-[12px] text-[#6b7280] border border-[#1c2333] px-2.5 py-1 rounded-md cursor-pointer hover:border-[#232b3e] transition-colors">
          <Circle size={6} fill="#22c55e" className="text-green-500" />
          Production
          <ChevronDown size={12} />
        </div>

        <button className="text-[#4b5563] hover:text-[#9ca3af] transition-colors relative p-1">
          <Bell size={16} />
          <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 bg-blue-500 rounded-full" />
        </button>

        <div className="w-7 h-7 rounded-md bg-[#1c2333] flex items-center justify-center text-[#6b7280] cursor-pointer hover:bg-[#232b3e] transition-colors">
          <User size={14} />
        </div>
      </div>
    </header>
  );
}
