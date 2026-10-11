export type ActivityStatus = "started" | "completed";

export interface AgentActivity {
  id: string;
  message: string;
  status: ActivityStatus;
}

export interface AgentToolCall {
  id: string;
  name: string;
  label: string;
  status: ActivityStatus;
}

export interface DiscoveredSource {
  title: string;
  url: string;
  domain: string;
}

export interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
  attachedFiles?: string[];
  activities?: AgentActivity[];
  tools?: AgentToolCall[];
  executionTimeSeconds?: number;
}

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  history?: ChatHistoryMessage[];
  attached_files?: string[];
}

export interface ChatResponse {
  message: string;
}

export type StreamStatus = "analyzing" | "executing_tools";

export interface StreamStatusEvent {
  type: "status";
  status: StreamStatus;
  message?: string;
}

export interface StreamActivityEvent {
  type: "activity";
  id: string;
  message: string;
  status: ActivityStatus;
}

export interface StreamToolStartEvent {
  type: "tool_start";
  tool_name: string;
}

export interface StreamToolEndEvent {
  type: "tool_end";
  tool_name: string;
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
  | StreamStatusEvent
  | StreamActivityEvent
  | StreamToolStartEvent
  | StreamToolEndEvent
  | StreamTokenEvent
  | StreamErrorEvent
  | StreamCompleteEvent;

export type StreamEventCallback = (event: AgentStreamEvent) => void;

export interface ChatServiceContract {
  sendMessage(payload: ChatRequest): Promise<ChatResponse>;
  streamMessage(
    payload: ChatRequest,
    onEvent: StreamEventCallback,
    signal?: AbortSignal,
  ): Promise<void>;
}
