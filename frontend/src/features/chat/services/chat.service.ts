import { apiStream } from "@/shared/api/stream";
import {
  ChatServiceContract,
  AgentStreamEvent,
  ChatRequest,
  ChatResponse,
  StreamEventCallback,
} from "../types/chat.types";

export const chatService: ChatServiceContract = {
  async sendMessage(payload: ChatRequest): Promise<ChatResponse> {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${baseUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to send message");
    return res.json();
  },

  async streamMessage(
    payload: ChatRequest,
    onEvent: StreamEventCallback,
    signal?: AbortSignal,
  ): Promise<void> {
    return apiStream<AgentStreamEvent>(
      "/api/chat/stream",
      payload,
      onEvent,
      signal,
    );
  },
};
