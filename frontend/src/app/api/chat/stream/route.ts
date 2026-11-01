/**
 * Unbuffered Server-Sent Events (SSE) proxy route for `POST /api/chat/stream`.
 *
 * Why this Route Handler exists alongside `next.config.ts` `rewrites()`:
 * 1. First-Party Cookies: All `/api/*` requests are served from the Next.js origin
 *    so `HttpOnly; SameSite=Lax` session and guest cookies (`genchat_session`,
 *    `genchat_guest`) work identically in local development and across Vercel ->
 *    Cloud Run in production.
 * 2. Real-Time SSE Streaming: Next.js's built-in `rewrites()` proxy buffers/compresses
 *    upstream `text/event-stream` responses until the backend connection closes, which
 *    would delay rendering `AgentExecutionTimeline` activities and streamed tokens
 *    until the entire response finishes. This Route Handler takes precedence over
 *    `rewrites()` for `/api/chat/stream` and pipes the upstream `ReadableStream`
 *    directly with `Content-Encoding: none` and `Cache-Control: no-cache, no-transform`
 *    so every SSE frame flushes to the browser immediately.
 */

import { CHAT_STREAM_ENDPOINT } from "@/features/chat/constants/chat.constants";
import {
  buildProxyErrorResponse,
  buildProxyStreamResponse,
  buildUpstreamHeaders,
  resolveBackendOrigin,
} from "@/shared/api/stream";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  const body = await request.text();
  const upstreamUrl = `${resolveBackendOrigin()}${CHAT_STREAM_ENDPOINT}`;

  const upstream = await fetch(upstreamUrl, {
    method: "POST",
    headers: buildUpstreamHeaders(request),
    body,
    cache: "no-store",
    signal: request.signal,
  });

  if (!upstream.ok || !upstream.body) {
    return buildProxyErrorResponse(upstream);
  }

  return buildProxyStreamResponse(upstream);
}
