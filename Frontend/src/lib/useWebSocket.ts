"use client";

import { useEffect } from "react";
import { useGlobalWebSocket } from "@/providers/WebSocketProvider";
export type { WSMessage } from "@/providers/WebSocketProvider";

export function useWebSocket(topics?: string[]) {
  const { connected, send, subscribe } = useGlobalWebSocket();

  useEffect(() => {
    if (topics && topics.length > 0) {
      subscribe(topics);
    }
  }, [topics, subscribe]);

  return { connected, send };
}
