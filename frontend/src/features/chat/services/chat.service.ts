import { apiStream } from "@/shared/api/stream";
import {
  ChatServiceContract,
  AgentStreamEvent,
  ChatRequest,
  StreamEventCallback,
} from "../types/chat.types";

export const chatService: ChatServiceContract = {
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
