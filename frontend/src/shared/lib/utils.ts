import React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Flatten primitive text children of a React node into a single trimmed string.
 */
export function flattenChildrenText(children: React.ReactNode): string {
  const parts: string[] = [];
  React.Children.forEach(children, (child) => {
    if (typeof child === "string" || typeof child === "number") {
      parts.push(String(child));
    }
  });
  return parts.join(" ").trim();
}

/**
 * Validate and return a non-empty environment variable value, throwing a clear Error if absent.
 */
export function requireEnvValue(
  rawValue: string | undefined,
  errorMessage: string,
): string {
  const trimmed = rawValue?.trim();
  if (!trimmed) {
    throw new Error(errorMessage);
  }
  return trimmed;
}
