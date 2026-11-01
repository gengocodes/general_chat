export const LOGIN_REQUIRED_ERROR_CODE = "login_required";

export const DEFAULT_BACKEND_ORIGIN = "http://localhost:8000";

export const FORWARDED_REQUEST_HEADERS = [
  "content-type",
  "cookie",
  "origin",
  "referer",
  "x-forwarded-for",
] as const;

export const SSE_STREAM_HEADERS: Record<string, string> = {
  "Content-Type": "text/event-stream; charset=utf-8",
  "Cache-Control": "no-cache, no-transform",
  Connection: "keep-alive",
  "Content-Encoding": "none",
  "X-Accel-Buffering": "no",
};

export const DEFAULT_LOGIN_REQUIRED_MESSAGE =
  "You have used your free messages. Sign in with Google to continue.";

export const DEFAULT_API_ERROR_MESSAGE =
  "Failed to communicate with AI assistant.";

export const EMPTY_STREAM_ERROR_MESSAGE =
  "No response stream returned by the server.";
