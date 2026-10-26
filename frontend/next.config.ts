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
];

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
