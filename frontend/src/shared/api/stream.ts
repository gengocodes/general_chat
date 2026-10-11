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
 * Extracts error details from a failed HTTP response, with fallback handling.
 */
async function extractErrorMessage(response: Response): Promise<string> {
  const fallbackMessage = "Failed to communicate with AI assistant.";
  try {
    const jsonErr = (await response.json()) as { detail?: string };
    return jsonErr?.detail || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

/**
 * Shared HTTP SSE streaming client using native fetch and ReadableStream.
 */
export async function apiStream<T>(
  endpoint: string,
  payload: unknown,
  onEvent: (event: T) => void,
  signal?: AbortSignal,
): Promise<void> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const response = await fetch(`${baseUrl}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  if (!response.body) {
    throw new Error("No response stream returned by the server.");
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
