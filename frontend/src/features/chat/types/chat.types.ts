export type ActivityStatus = "started" | "completed";

export type PromptCategoryIcon =
  | "sparkles"
  | "files"
  | "code"
  | "pen"
  | "lightbulb";

export interface PromptSuggestion {
  label: string;
  prompt: string;
}

export interface PromptCategory {
  id: string;
  label: string;
  icon: PromptCategoryIcon;
  items: readonly PromptSuggestion[];
}

export interface AgentActivity {
  id: string;
  message: string;
  status: ActivityStatus;
}

export interface AttachedFileItem {
  objectKey: string;
  originalName: string;
  sizeBytes: number;
  downloadUrl: string;
}

export type FileValidationResult =
  | { valid: true }
  | { valid: false; error: string };

export interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
  attachedFiles?: AttachedFileItem[];
  activities?: AgentActivity[];
  executionTimeSeconds?: number;
}

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  history: ChatHistoryMessage[];
  attached_files: string[];
}

export interface FileUploadResponse {
  filename: string;
  original_name: string;
  size_bytes: number;
  download_url: string;
}

export interface StreamActivityEvent {
  type: "activity";
  id: string;
  message: string;
  status: ActivityStatus;
}

export interface StreamTokenEvent {
  type: "token";
  token: string;
}

export interface StreamErrorEvent {
  type: "error";
  error: string;
}

export interface StreamCompleteEvent {
  type: "complete";
}

export type AgentStreamEvent =
  | StreamActivityEvent
  | StreamTokenEvent
  | StreamErrorEvent
  | StreamCompleteEvent;

export type StreamEventCallback = (event: AgentStreamEvent) => void;

export interface ChatServiceContract {
  streamMessage(
    payload: ChatRequest,
    onEvent: StreamEventCallback,
    signal?: AbortSignal,
  ): Promise<void>;
  uploadFile(file: File): Promise<FileUploadResponse>;
}
