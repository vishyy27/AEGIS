"use client";

import { useEffect } from "react";
import { useGlobalWebSocket } from "@/providers/WebSocketProvider";
export type { WSMessage } from "@/providers/WebSocketProvider";

export function useWebSocket(topics?: string[]) {
  const { messages, lastMessage, connected, send, subscribe } = useGlobalWebSocket();

  useEffect(() => {
    if (topics && topics.length > 0) {
      subscribe(topics);
    }
  }, [topics, subscribe]);

  // Filter messages client-side if a component specific topic list was passed.
  // Actually, for UI simplicity, we can just return all messages, or filter them based on topic prefix.
  // The backend doesn't attach topic names directly to events usually, so we just return the stream.
  return { messages, lastMessage, connected, send };
}
