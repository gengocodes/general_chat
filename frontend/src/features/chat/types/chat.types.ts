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
    signal: AbortSignal,
  ): Promise<void>;
  uploadFile(file: File): Promise<FileUploadResponse>;
}

export interface ChatStoreState {
  messages: ChatMessageItem[];
  attachedFiles: AttachedFileItem[];
  addMessage: (msg: ChatMessageItem) => void;
  removeMessagesByIds: (ids: string[]) => void;
  appendMessageContent: (id: string, chunk: string) => void;
  updateMessageActivity: (msgId: string, activity: AgentActivity) => void;
  setExecutionTime: (msgId: string, durationSeconds: number) => void;
  finalizeMessageActivities: (msgId: string) => void;
  addAttachedFile: (file: AttachedFileItem) => void;
  removeAttachedFile: (objectKey: string) => void;
  clearAttachedFiles: () => void;
}

export interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  onSend: (message: string) => void;
  onCancel: () => void;
  isSending: boolean;
  attachedFiles: AttachedFileItem[];
  onAddFile: (file: AttachedFileItem) => void;
  onRemoveFile: (objectKey: string) => void;
  showDisclaimer?: boolean;
  disabled: boolean;
}

export interface ChatMessageProps {
  message: ChatMessageItem;
}

export interface AgentAvatarProps {
  className?: string;
}

export interface UserAvatarProps {
  className?: string;
}

export interface AgentExecutionTimelineProps {
  activities?: AgentActivity[];
  executionTimeSeconds?: number;
}

export interface PromptCategorySelectorProps {
  onHoverPrompt: (prompt: string | null) => void;
  onSelectPrompt: (prompt: string) => void;
}
