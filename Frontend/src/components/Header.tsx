"use client";

import React, { useState, useEffect } from "react";
import { Search, Bell, User, ChevronDown, Circle, ServerCrash, Rocket, Activity, CheckCircle2, ShieldAlert } from "lucide-react";
import { useGlobalWebSocket } from "@/providers/WebSocketProvider";
import { fetchAPI } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";

interface SearchResult {
  id: number;
  service: string;
  repo_name: string;
  risk_level: string;
  risk_score: number;
  commit_hash: string;
}

export default function Header() {
  const { connected } = useGlobalWebSocket();
  const [mounted, setMounted] = useState(false);
  const [apiHealth, setApiHealth] = useState<"up" | "down" | "checking">("checking");
  const [searchFocused, setSearchFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    const checkHealth = async () => {
      try {
        const res = await fetchAPI<{ status: string }>("/health", { skipCache: true });
        setApiHealth(res.status ? "up" : "down");
      } catch {
        setApiHealth("down");
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await fetchAPI<SearchResult[]>(`/api/deployments/?search=${encodeURIComponent(searchQuery)}&limit=5`);
        setSearchResults(res || []);
      } catch (err) {
        console.error("Search failed", err);
      } finally {
        setIsSearching(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSearchSubmit = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      setSearchFocused(false);
      router.push(`/deployments?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <header className="h-14 fixed top-0 left-[220px] right-0 bg-[#0a0e1a]/95 backdrop-blur-md border-b border-[#1c2333] flex items-center justify-between px-6 z-40 transition-colors">
      <div className="relative">
        <div className={`flex items-center bg-[#0f1422] border rounded-md px-3 py-1.5 w-96 gap-2 transition-all ${
          searchFocused ? "border-blue-500/30 ring-1 ring-blue-500/10" : "border-[#1c2333]"
        }`}>
          <Search size={14} className={searchFocused ? "text-blue-400" : "text-[#4b5563]"} />
          <input
            type="text"
            placeholder="Search deployments by service, repo, or hash..."
            className="bg-transparent border-none text-[13px] text-white outline-none w-full placeholder:text-[#3d4454]"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchSubmit}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setTimeout(() => setSearchFocused(false), 200)}
          />
          <div className="hidden md:flex items-center gap-1 shrink-0 bg-[#151a2e] border border-[#1c2333] rounded px-1.5 py-0.5 text-[9px] text-[#4a5468] font-medium mono">
            <span>⌘</span><span>K</span>
          </div>
        </div>

        <AnimatePresence>
          {searchFocused && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className="absolute top-full left-0 mt-2 w-full bg-[#0f1422] border border-[#1c2333] rounded-lg shadow-xl overflow-hidden py-2 z-50"
            >
              {apiHealth === "down" ? (
                <div className="px-3 py-4 text-center flex flex-col items-center gap-2 text-[#4a5468]">
                  <ServerCrash size={16} className="text-rose-500/50" />
                  <span className="text-[12px]">Backend is not running</span>
                </div>
              ) : searchQuery.length > 0 ? (
                <div className="flex flex-col">
                  {isSearching ? (
                    <div className="px-3 py-4 text-center text-[12px] text-[#4a5468] flex items-center justify-center gap-2">
                      <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                      Searching...
                    </div>
                  ) : searchResults.length > 0 ? (
                    <>
                      <div className="px-3 py-1.5 text-[10px] text-[#4a5468] uppercase tracking-wider font-semibold border-b border-[#1c2333]">
                        Deployments
                      </div>
                      {searchResults.map(result => (
                        <div 
                          key={result.id} 
                          className="px-3 py-2.5 hover:bg-[#151a2e] cursor-pointer flex items-center justify-between border-b border-[#1c2333] last:border-0 transition-colors"
                          onClick={() => router.push(`/deployments?search=${encodeURIComponent(result.service)}`)}
                        >
                          <div className="flex items-center gap-2.5">
                            <Rocket size={14} className="text-[#8892a8]" />
                            <div className="flex flex-col">
                              <span className="text-[12px] font-medium text-white">{result.service}</span>
                              <span className="text-[10px] text-[#4a5468] mono">{result.commit_hash?.slice(0, 7) || 'N/A'} • {result.repo_name}</span>
                            </div>
                          </div>
                          <div className={`px-1.5 py-0.5 rounded text-[10px] font-medium border flex items-center gap-1 ${
                            result.risk_level === 'HIGH' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                            result.risk_level === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                            'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          }`}>
                            {result.risk_level === 'HIGH' ? <ShieldAlert size={10} /> : result.risk_level === 'MEDIUM' ? <Activity size={10} /> : <CheckCircle2 size={10} />}
                            {result.risk_score}%
                          </div>
                        </div>
                      ))}
                    </>
                  ) : (
                    <div className="px-3 py-4 text-center text-[12px] text-[#4a5468]">
                      No results found for "{searchQuery}"
                    </div>
                  )}
                </div>
              ) : (
                <div className="px-3 py-2 text-[11px] text-[#4a5468] uppercase tracking-wider font-semibold">
                  Start typing to search
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="flex items-center gap-4">
        {mounted && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-[11px] font-medium px-2 py-1 rounded bg-[#0f1422] border border-[#1c2333] text-[#4a5468] uppercase tracking-wide cursor-help" title="Backend API Status">
              {apiHealth === "checking" ? (
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
              ) : apiHealth === "up" ? (
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
              ) : (
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]" />
              )}
              {apiHealth === "checking" ? "CHECKING" : apiHealth === "up" ? "API ONLINE" : "API OFFLINE"}
            </div>

            <div className="flex items-center gap-1.5 text-[11px] font-medium px-2 py-1 rounded bg-[#0f1422] border border-[#1c2333] text-[#4a5468] uppercase tracking-wide cursor-help" title="WebSocket Status">
              <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]'}`} />
              {connected ? 'WS ONLINE' : 'WS OFFLINE'}
            </div>
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
