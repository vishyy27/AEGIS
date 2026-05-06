"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Send, Sparkles, X, Minimize2, Maximize2 } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface Message {
  role: string;
  content: string;
  timestamp?: string;
}

export default function AICommandBar() {
  const [open, setOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetchAPI<{ session_id: string; response: string }>("/api/assistant/chat", {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId, message: userMsg }),
      });
      setSessionId(res.session_id);
      setMessages(prev => [...prev, { role: "assistant", content: res.response }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "⚠️ Failed to get response. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!open) {
    return (
      <motion.button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-900/30 hover:shadow-cyan-500/30 transition-all hover:scale-105 active:scale-95"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <Sparkles size={24} className="text-white" />
      </motion.button>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        className={`fixed bottom-6 right-6 z-50 ${minimized ? "w-80" : "w-[420px]"} glass-card shadow-2xl shadow-black/40 overflow-hidden`}
        style={{ maxHeight: minimized ? "52px" : "600px" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-cyan-600/20 to-blue-600/20 border-b border-slate-700/50">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-cyan-400" />
            <span className="text-sm font-semibold text-slate-200">AEGIS AI Assistant</span>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={() => setMinimized(!minimized)} className="p-1 hover:bg-slate-700/50 rounded transition-colors">
              {minimized ? <Maximize2 size={14} className="text-slate-400" /> : <Minimize2 size={14} className="text-slate-400" />}
            </button>
            <button onClick={() => setOpen(false)} className="p-1 hover:bg-slate-700/50 rounded transition-colors">
              <X size={14} className="text-slate-400" />
            </button>
          </div>
        </div>

        {!minimized && (
          <>
            {/* Messages */}
            <div ref={scrollRef} className="h-[420px] overflow-y-auto p-4 space-y-3">
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <Sparkles size={32} className="text-cyan-500/30 mx-auto mb-3" />
                  <p className="text-sm text-slate-400">Ask me about your deployments</p>
                  <div className="mt-4 space-y-2">
                    {["Why was my deployment blocked?", "Which services are unstable?", "Show deployment trends"].map((q) => (
                      <button key={q} onClick={() => { setInput(q); }} className="block w-full text-left text-xs text-slate-500 hover:text-cyan-400 bg-slate-800/50 hover:bg-slate-800 px-3 py-2 rounded-lg transition-colors">
                        &ldquo;{q}&rdquo;
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((msg, i) => (
                <motion.div
                  key={i} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                    msg.role === "user"
                      ? "bg-cyan-600/20 text-cyan-100 border border-cyan-500/20"
                      : "bg-slate-800/80 text-slate-300 border border-slate-700/50"
                  }`}>
                    <div className="whitespace-pre-wrap text-xs leading-relaxed">{msg.content}</div>
                  </div>
                </motion.div>
              ))}
              {loading && (
                <div className="flex items-center gap-2 text-slate-500 text-xs">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                  Thinking...
                </div>
              )}
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t border-slate-700/50 bg-slate-900/50">
              <div className="flex items-center gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Ask about deployments, risks, services..."
                  className="flex-1 bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 outline-none focus:border-cyan-500/50 transition-colors"
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="p-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 rounded-lg transition-colors"
                >
                  <Send size={16} className="text-white" />
                </button>
              </div>
            </div>
          </>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
