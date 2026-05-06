"use client";

import React, { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { fetchAPI } from "@/lib/api";

interface Message { role: string; content: string; timestamp?: string; }
interface Session { session_id: string; title: string; message_count: number; }

const suggestions = [
  "Why was my deployment blocked?",
  "Which services are unstable?",
  "Show deployment trends",
  "What caused the last incident?",
  "System overview",
];

export default function AIAssistantPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAPI<Session[]>("/api/assistant/sessions").then(setSessions).catch(() => {});
  }, []);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const loadSession = async (sid: string) => {
    setActiveSession(sid);
    const msgs = await fetchAPI<Message[]>(`/api/assistant/sessions/${sid}/messages`);
    setMessages(msgs);
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const res = await fetchAPI<{ session_id: string; response: string }>("/api/assistant/chat", {
        method: "POST", body: JSON.stringify({ session_id: activeSession, message: text }),
      });
      setActiveSession(res.session_id);
      setMessages(prev => [...prev, { role: "assistant", content: res.response }]);
      // Refresh sessions list
      fetchAPI<Session[]>("/api/assistant/sessions").then(setSessions).catch(() => {});
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "Unable to process. Try again." }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title">AI Assistant</h1>
        <p className="text-muted mt-0.5">Operational intelligence powered by real deployment data</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4" style={{ height: "calc(100vh - 180px)" }}>
        {/* Sessions */}
        <div className="aegis-card lg:col-span-1 flex flex-col overflow-hidden">
          <div className="flex items-center justify-between mb-3 shrink-0">
            <h3 className="section-title">Sessions</h3>
            <button onClick={() => { setActiveSession(null); setMessages([]); }}
              className="text-[11px] text-blue-400 hover:text-blue-300 transition-colors">New</button>
          </div>
          <div className="space-y-0.5 overflow-y-auto flex-1">
            {sessions.map(s => (
              <button key={s.session_id} onClick={() => loadSession(s.session_id)}
                className={`w-full text-left px-2.5 py-2 rounded-md text-[12px] transition-colors ${
                  activeSession === s.session_id ? "bg-white/[0.05] text-white" : "text-[#6b7280] hover:bg-white/[0.02]"
                }`}>
                <div className="truncate">{s.title}</div>
                <div className="text-[10px] text-[#3d4454] mt-0.5">{s.message_count} messages</div>
              </button>
            ))}
          </div>
        </div>

        {/* Chat */}
        <div className="lg:col-span-3 aegis-card flex flex-col overflow-hidden">
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full">
                <p className="text-[14px] font-medium text-[#8892a8] mb-1">Ask about your deployments</p>
                <p className="text-[12px] text-[#4a5468] mb-5">Responses use real deployment data — never fabricated.</p>
                <div className="grid grid-cols-2 gap-2 max-w-md">
                  {suggestions.map(q => (
                    <button key={q} onClick={() => setInput(q)}
                      className="text-left text-[11px] text-[#6b7280] hover:text-blue-400 bg-[#0a0e1a] hover:bg-[#0f1422] px-3 py-2.5 rounded-md border border-[#1c2333] hover:border-blue-500/15 transition-colors">
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[70%] rounded-lg px-3.5 py-2.5 ${
                    msg.role === "user"
                      ? "bg-blue-600/12 text-blue-200 border border-blue-500/12"
                      : "bg-[#151a2e] text-[#c8cdd8] border border-[#1c2333]"
                  }`}>
                    <pre className="whitespace-pre-wrap text-[12px] leading-relaxed font-[inherit] m-0">{msg.content}</pre>
                  </div>
                </motion.div>
              ))
            )}
            {loading && (
              <div className="flex gap-1 items-center text-[#4a5468] text-[11px]">
                <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            )}
          </div>

          <div className="border-t border-[#1c2333] p-3 shrink-0">
            <div className="flex items-center gap-2">
              <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()}
                placeholder="Ask about deployments, risks, incidents..."
                className="flex-1 bg-[#0a0e1a] border border-[#1c2333] rounded-md px-3.5 py-2.5 text-[13px] text-white placeholder:text-[#3d4454] outline-none focus:border-blue-500/30 transition-colors" />
              <button onClick={send} disabled={loading || !input.trim()}
                className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-[13px] font-medium transition-colors disabled:opacity-30 active:scale-[0.98]">
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
