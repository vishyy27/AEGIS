"use client";

import React, { useState, useEffect } from "react";
import { Search, Bell, User, ChevronDown, Circle } from "lucide-react";
import { useGlobalWebSocket } from "@/providers/WebSocketProvider";

export default function Header() {
  const { connected } = useGlobalWebSocket();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  return (
    <header className="h-14 fixed top-0 left-[220px] right-0 bg-[#0a0e1a]/95 backdrop-blur-md border-b border-[#1c2333] flex items-center justify-between px-6 z-40 transition-colors">
      <div className="flex items-center bg-[#0f1422] border border-[#1c2333] rounded-md px-3 py-1.5 w-80 gap-2 focus-within:border-blue-500/30 focus-within:ring-1 focus-within:ring-blue-500/10 transition-all">
        <Search size={14} className="text-[#4b5563]" />
        <input
          type="text"
          placeholder="Search deployments..."
          className="bg-transparent border-none text-[13px] text-white outline-none w-full placeholder:text-[#3d4454]"
        />
        <div className="hidden md:flex items-center gap-1 shrink-0 bg-[#151a2e] border border-[#1c2333] rounded px-1.5 py-0.5 text-[9px] text-[#4a5468] font-medium mono">
          <span>⌘</span><span>K</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {mounted && (
          <div className="flex items-center gap-1.5 text-[11px] font-medium px-2 py-1 rounded bg-[#0f1422] border border-[#1c2333] text-[#4a5468] uppercase tracking-wide">
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-500 animate-live-dot' : 'bg-rose-500'}`} />
            {connected ? 'WS ONLINE' : 'WS OFFLINE'}
          </div>
        )}
        
        <div className="flex items-center gap-1.5 text-[12px] text-[#8892a8] border border-[#1c2333] px-2.5 py-1.5 rounded-md cursor-pointer hover:bg-[#151a2e] transition-colors">
          <Circle size={8} className="text-emerald-500 fill-emerald-500/20" />
          Production
          <ChevronDown size={12} className="text-[#4a5468] ml-1" />
        </div>

        <button className="text-[#4b5563] hover:text-[#c8cdd8] transition-colors relative p-1.5 hover:bg-[#151a2e] rounded-md">
          <Bell size={15} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-blue-500 rounded-full ring-2 ring-[#0a0e1a]" />
        </button>

        <div className="w-8 h-8 rounded-md bg-gradient-to-br from-[#1c2333] to-[#0f1422] border border-[#1c2333] flex items-center justify-center text-[#8892a8] cursor-pointer hover:border-[#3d4454] transition-colors overflow-hidden">
          <User size={14} />
        </div>
      </div>
    </header>
  );
}
