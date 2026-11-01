import type { NextConfig } from "next";

const CSP_HOST_SOURCE_PATTERN =
  /^(https?:\/\/)?(\*\.)?[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(:\d+)?$/;

/**
 * Parse and validate the comma-separated ALLOWED_DOMAINS environment variable
 * into a list of valid Content-Security-Policy frame-ancestors host sources.
 */
function parseAllowedFrameAncestors(rawEnv: string | undefined): string[] {
  if (!rawEnv) {
    return [];
  }

  return rawEnv
    .split(",")
    .map((entry) => entry.trim().replace(/\/+$/, ""))
    .filter((entry) => entry.length > 0)
    .map((entry) => {
      if (!CSP_HOST_SOURCE_PATTERN.test(entry)) {
        throw new Error(
          `Invalid domain entry in ALLOWED_DOMAINS: "${entry}". Expected an origin or host pattern such as "https://example.com" or "https://*.example.com".`,
        );
      }
      return entry;
    });
}

const allowedAncestors = parseAllowedFrameAncestors(process.env.ALLOWED_DOMAINS);
const frameAncestorsValue = ["'self'", ...allowedAncestors].join(" ");

const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: `frame-ancestors ${frameAncestorsValue};`,
  },
  ...(allowedAncestors.length === 0
    ? [
        {
          key: "X-Frame-Options",
          value: "SAMEORIGIN",
        },
      ]
    : []),
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  {
    key: "Cross-Origin-Opener-Policy",
    value: "same-origin-allow-popups",
  },
];

const backendOrigin = (
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000"
).replace(/\/+$/, "");

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
  /**
   * Proxy `/api/*` requests to the FastAPI backend so `HttpOnly; SameSite=Lax`
   * session and guest cookies remain first-party on the frontend origin.
   * Note: `POST /api/chat/stream` is handled by `src/app/api/chat/stream/route.ts`
   * (which takes precedence over `rewrites`) so SSE frames stream without proxy buffering.
   */
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
