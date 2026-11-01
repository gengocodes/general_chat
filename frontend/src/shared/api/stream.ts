import {
  DEFAULT_API_ERROR_MESSAGE,
  DEFAULT_BACKEND_ORIGIN,
  DEFAULT_LOGIN_REQUIRED_MESSAGE,
  EMPTY_STREAM_ERROR_MESSAGE,
  FORWARDED_REQUEST_HEADERS,
  LOGIN_REQUIRED_ERROR_CODE,
  SSE_STREAM_HEADERS,
} from "./api.constants";
import { FastApiErrorPayload } from "./api.types";

export class LoginRequiredApiError extends Error {
  constructor(message: string = DEFAULT_LOGIN_REQUIRED_MESSAGE) {
    super(message);
    this.name = "LoginRequiredApiError";
  }
}

/**
 * Resolves the upstream backend origin for server-side route handlers.
 */
export function resolveBackendOrigin(): string {
  const rawOrigin =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    DEFAULT_BACKEND_ORIGIN;
  return rawOrigin.replace(/\/+$/, "");
}

/**
 * Builds forwarded request headers for upstream SSE proxy calls.
 * Requests uncompressed (`identity`) responses so Node's fetch does not buffer
 * compressed SSE frames.
 */
export function buildUpstreamHeaders(request: Request): Headers {
  const headers = new Headers({
    "Accept-Encoding": "identity",
  });

  for (const headerName of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(headerName);
    if (value !== null) {
      headers.set(headerName, value);
    }
  }

  return headers;
}

/**
 * Copies all Set-Cookie headers from an upstream response onto the target Headers.
 */
export function appendSetCookieHeaders(source: Headers, target: Headers): void {
  for (const cookie of source.getSetCookie()) {
    target.append("Set-Cookie", cookie);
  }
}

/**
 * Forwards an upstream non-2xx or empty-body response while preserving status,
 * Content-Type, Retry-After, and Set-Cookie headers.
 */
export async function buildProxyErrorResponse(
  upstream: Response,
): Promise<Response> {
  const errorHeaders = new Headers();
  const contentType = upstream.headers.get("content-type");
  if (contentType !== null) {
    errorHeaders.set("Content-Type", contentType);
  }
  const retryAfter = upstream.headers.get("retry-after");
  if (retryAfter !== null) {
    errorHeaders.set("Retry-After", retryAfter);
  }
  appendSetCookieHeaders(upstream.headers, errorHeaders);

  return new Response(await upstream.text(), {
    status: upstream.status,
    headers: errorHeaders,
  });
}

/**
 * Wraps an upstream SSE ReadableStream with anti-buffering headers and forwards
 * any Set-Cookie headers (e.g. newly issued HttpOnly guest cookies).
 */
export function buildProxyStreamResponse(upstream: Response): Response {
  const responseHeaders = new Headers(SSE_STREAM_HEADERS);
  appendSetCookieHeaders(upstream.headers, responseHeaders);

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

/**
 * Safely parses a single Server-Sent Event payload line (e.g. "data: {...}").
 * Returns the parsed event typed as T, or null if the line is not a valid SSE payload.
 */
function parseSSEEvent<T>(line: string): T | null {
  const trimmed = line.trim();
  if (!trimmed.startsWith("data:")) {
    return null;
  }

  const jsonStr = trimmed.slice(5).trim();
  if (!jsonStr) {
    return null;
  }

  try {
    return JSON.parse(jsonStr) as T;
  } catch {
    return null;
  }
}

/**
 * Inspects a failed HTTP response and returns LoginRequiredApiError when the
 * server responds with 401 and code === "login_required", or returns a readable
 * Error for all other error cases.
 */
export async function parseErrorResponse(
  response: Response,
  fallbackMessage: string = DEFAULT_API_ERROR_MESSAGE,
): Promise<Error> {
  try {
    const jsonErr = (await response.json()) as FastApiErrorPayload;
    const detail = jsonErr?.detail;
    if (
      response.status === 401 &&
      typeof detail === "object" &&
      detail !== null &&
      detail.code === LOGIN_REQUIRED_ERROR_CODE
    ) {
      return new LoginRequiredApiError(detail.message);
    }
    if (typeof detail === "string" && detail.length > 0) {
      return new Error(detail);
    }
    if (
      typeof detail === "object" &&
      detail !== null &&
      typeof detail.message === "string" &&
      detail.message.length > 0
    ) {
      return new Error(detail.message);
    }
    return new Error(fallbackMessage);
  } catch {
    return new Error(fallbackMessage);
  }
}

/**
 * Shared HTTP SSE streaming client using native fetch and ReadableStream.
 * Calls same-origin `/api/*` endpoints so cookies stay first-party.
 */
export async function apiStream<T>(
  endpoint: string,
  payload: unknown,
  onEvent: (event: T) => void,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(endpoint, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  if (!response.body) {
    throw new Error(EMPTY_STREAM_ERROR_MESSAGE);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const event = parseSSEEvent<T>(line);
        if (event !== null) {
          onEvent(event);
        }
      }
    }

    const trailingEvent = parseSSEEvent<T>(buffer);
    if (trailingEvent !== null) {
      onEvent(trailingEvent);
    }
  } finally {
    reader.releaseLock();
  }
}
