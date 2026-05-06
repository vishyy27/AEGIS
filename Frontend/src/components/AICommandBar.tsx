"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Send, Sparkles, X, Minus } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface Message { role: string; content: string; }

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
    const text = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await fetchAPI<{ session_id: string; response: string }>("/api/assistant/chat", {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });
      setSessionId(res.session_id);
      setMessages(prev => [...prev, { role: "assistant", content: res.response }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "Unable to process. Try again." }]);
    } finally { setLoading(false); }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-50 w-10 h-10 rounded-lg bg-blue-600 hover:bg-blue-500 flex items-center justify-center shadow-lg transition-all active:scale-95"
      >
        <MessageSquare size={16} className="text-white" />
      </button>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 12, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 12, scale: 0.97 }}
        className={`fixed bottom-5 right-5 z-50 w-[380px] glass-card shadow-2xl shadow-black/50 overflow-hidden flex flex-col`}
        style={{ maxHeight: minimized ? "44px" : "520px" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-[#1c2333] shrink-0">
          <div className="flex items-center gap-2">
            <Sparkles size={13} className="text-blue-400" />
            <span className="text-[12px] font-medium text-[#c8cdd8]">AEGIS Assistant</span>
          </div>
          <div className="flex items-center gap-0.5">
            <button onClick={() => setMinimized(!minimized)} className="p-1 hover:bg-white/[0.05] rounded transition-colors">
              <Minus size={12} className="text-[#4b5563]" />
            </button>
            <button onClick={() => setOpen(false)} className="p-1 hover:bg-white/[0.05] rounded transition-colors">
              <X size={12} className="text-[#4b5563]" />
            </button>
          </div>
        </div>

        {!minimized && (
          <>
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2.5 min-h-0">
              {messages.length === 0 && (
                <div className="flex flex-col items-center py-12">
                  <p className="text-[12px] text-[#4a5468] mb-3">Ask about deployments, risks, or incidents</p>
                  {["Why was my deploy blocked?", "System overview", "Unstable services"].map(q => (
                    <button key={q} onClick={() => setInput(q)}
                      className="text-[11px] text-[#4b5563] hover:text-blue-400 bg-[#0f1422] hover:bg-[#151a2e] w-full text-left px-3 py-2 rounded-md mb-1 border border-[#1c2333] transition-colors">
                      {q}
                    </button>
                  ))}
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] rounded-lg px-3 py-2 text-[12px] leading-relaxed ${
                    msg.role === "user"
                      ? "bg-blue-600/15 text-blue-200 border border-blue-500/15"
                      : "bg-[#151a2e] text-[#c8cdd8] border border-[#1c2333]"
                  }`}>
                    <pre className="whitespace-pre-wrap font-[inherit] m-0">{msg.content}</pre>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex gap-1 items-center text-[#4a5468] text-[11px] px-1">
                  <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              )}
            </div>

            <div className="px-3 py-2.5 border-t border-[#1c2333] shrink-0">
              <div className="flex items-center gap-2">
                <input
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && sendMessage()}
                  placeholder="Ask something..."
                  className="flex-1 bg-[#0f1422] border border-[#1c2333] rounded-md px-3 py-1.5 text-[12px] text-white placeholder:text-[#3d4454] outline-none focus:border-blue-500/30 transition-colors"
                />
                <button onClick={sendMessage} disabled={loading || !input.trim()}
                  className="p-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-[#1c2333] rounded-md transition-colors">
                  <Send size={12} className="text-white" />
                </button>
              </div>
            </div>
          </>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
