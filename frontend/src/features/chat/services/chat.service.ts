import {
  API_BASE_URL,
  apiStream,
  extractErrorMessage,
} from "@/shared/api/stream";
import {
  ChatServiceContract,
  AgentStreamEvent,
  ChatRequest,
  FileUploadResponse,
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

  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/files/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(
        await extractErrorMessage(response, "File upload failed."),
      );
    }

    return (await response.json()) as FileUploadResponse;
  },
};
