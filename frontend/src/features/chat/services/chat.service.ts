import { apiStream, parseErrorResponse } from "@/shared/api/stream";
import {
  CHAT_STREAM_ENDPOINT,
  FILE_UPLOAD_ENDPOINT,
  FILE_UPLOAD_ERROR_MESSAGE,
} from "../constants/chat.constants";
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
    signal: AbortSignal,
  ): Promise<void> {
    return apiStream<AgentStreamEvent>(
      CHAT_STREAM_ENDPOINT,
      payload,
      onEvent,
      signal,
    );
  },

  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(FILE_UPLOAD_ENDPOINT, {
      method: "POST",
      credentials: "include",
      body: formData,
    });

    if (!response.ok) {
      throw await parseErrorResponse(response, FILE_UPLOAD_ERROR_MESSAGE);
    }

    return (await response.json()) as FileUploadResponse;
  },
};
