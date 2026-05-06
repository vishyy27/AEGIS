"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { MessageSquare, Plus, Sparkles } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface Message { role: string; content: string; timestamp?: string; }
interface Session { session_id: string; title: string; message_count: number; created_at: string; }

export default function AIAssistantPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);

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

  const sendMessage = async () => {
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
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "⚠️ Error getting response" }]);
    } finally { setLoading(false); }
  };

  const quickQueries = [
    "Why was my latest deployment blocked?",
    "Which services are most unstable?",
    "Show me deployment trends",
    "What caused the last incident?",
    "Give me a system overview",
    "Show confidence drops",
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title text-gradient-purple">AI DevOps Assistant</h1>
        <p className="text-muted mt-1">Conversational operational intelligence powered by real deployment data</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6" style={{ minHeight: "70vh" }}>
        {/* Sessions sidebar */}
        <div className="aegis-card lg:col-span-1">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-300">Sessions</h3>
            <button onClick={() => { setActiveSession(null); setMessages([]); }} className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors">
              <Plus size={14} className="text-cyan-400" />
            </button>
          </div>
          <div className="space-y-1">
            {sessions.map(s => (
              <button key={s.session_id} onClick={() => loadSession(s.session_id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${activeSession === s.session_id ? "bg-slate-800 text-cyan-400" : "text-slate-400 hover:bg-slate-800/50"}`}>
                <div className="truncate">{s.title}</div>
                <div className="text-[10px] text-slate-600">{s.message_count} messages</div>
              </button>
            ))}
          </div>
        </div>

        {/* Chat area */}
        <div className="lg:col-span-3 aegis-card flex flex-col">
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[400px]">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full">
                <Sparkles size={48} className="text-violet-500/20 mb-4" />
                <h2 className="text-lg font-semibold text-slate-300 mb-2">Ask me anything about your deployments</h2>
                <p className="text-sm text-slate-500 mb-6">I use real deployment data — never fake telemetry.</p>
                <div className="grid grid-cols-2 gap-2 max-w-lg">
                  {quickQueries.map(q => (
                    <button key={q} onClick={() => setInput(q)}
                      className="text-left text-xs text-slate-400 hover:text-cyan-400 bg-slate-800/50 hover:bg-slate-800 px-3 py-2.5 rounded-lg transition-colors border border-slate-800 hover:border-cyan-500/20">
                      &ldquo;{q}&rdquo;
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[75%] rounded-xl px-4 py-3 ${
                    msg.role === "user" ? "bg-cyan-600/15 border border-cyan-500/20 text-cyan-100" : "bg-slate-800/60 border border-slate-700/50 text-slate-300"
                  }`}>
                    <pre className="whitespace-pre-wrap text-sm leading-relaxed font-[inherit]">{msg.content}</pre>
                  </div>
                </motion.div>
              ))
            )}
            {loading && (
              <div className="flex gap-1.5 items-center text-slate-500 text-sm">
                <span className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                <span className="ml-2">Analyzing...</span>
              </div>
            )}
          </div>

          {/* Input bar */}
          <div className="border-t border-slate-800 p-4">
            <div className="flex items-center gap-3">
              <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && sendMessage()}
                placeholder="Ask about deployments, risks, services, incidents..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-600 outline-none focus:border-cyan-500/50 transition-colors" />
              <button onClick={sendMessage} disabled={loading || !input.trim()}
                className="px-5 py-3 bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white rounded-xl font-medium text-sm transition-all disabled:opacity-40 active:scale-95">
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
