export type FileKind = "pdf" | "docx" | "code" | "text" | "generic";

const UUID_PREFIX_REGEX = /^[0-9a-fA-F]{12}_/;

/**
 * Strip the 12-hex UUID prefix from a stored object key or URL segment
 * so the user always sees a clean human-readable filename.
 */
export function extractCleanFilename(keyOrFilename: string): string {
  const decoded = decodeURIComponent(keyOrFilename.trim());
  const baseSegment = decoded.split("?")[0].split("/").pop() || decoded;
  return baseSegment.replace(UUID_PREFIX_REGEX, "");
}

/**
 * Extract the uppercase file extension (e.g. "PDF", "DOCX", "TXT").
 */
export function getFileExtension(filename: string): string {
  const clean = extractCleanFilename(filename);
  const parts = clean.split(".");
  if (parts.length < 2) return "FILE";
  return (parts.pop() || "FILE").toUpperCase();
}

/**
 * Classify a filename into a semantic FileKind for icon and badge styling.
 */
export function getFileKind(filename: string): FileKind {
  const ext = getFileExtension(filename).toLowerCase();
  if (ext === "pdf") return "pdf";
  if (ext === "docx" || ext === "doc") return "docx";
  if (
    ["ts", "tsx", "js", "jsx", "py", "json", "html", "css", "sql", "sh"].includes(
      ext,
    )
  ) {
    return "code";
  }
  if (["txt", "md", "csv", "log"].includes(ext)) {
    return "text";
  }
  return "generic";
}

/**
 * Format raw byte count into a concise human-readable string (e.g. "142 KB", "1.8 MB").
 */
export function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb < 10 ? kb.toFixed(1) : Math.round(kb)} KB`;
  const mb = kb / 1024;
  return `${mb.toFixed(1)} MB`;
}

/**
 * Check whether a URL points to a Gengo file download endpoint or Cloudflare R2 presigned URL.
 */
export function isFileDownloadUrl(href?: string): boolean {
  if (!href) return false;
  return (
    href.startsWith("/api/files/download/") ||
    href.includes("/api/files/download/") ||
    href.includes("r2.cloudflarestorage.com") ||
    href.includes("X-Amz-Signature=")
  );
}

/**
 * Extract a displayable filename from either a markdown link label or a download URL.
 */
export function resolveDownloadFilename(href: string, labelText: string): string {
  const trimmedLabel = labelText.trim();
  if (/\.(pdf|docx|doc|txt|md|csv|json)$/i.test(trimmedLabel)) {
    return extractCleanFilename(trimmedLabel);
  }
  try {
    const url = new URL(href, "http://localhost");
    const disposition = url.searchParams.get("response-content-disposition");
    if (disposition) {
      const match = disposition.match(/filename="?([^";]+)"?/i);
      if (match?.[1]) {
        return extractCleanFilename(match[1]);
      }
    }
    const pathSegment = url.pathname.split("/").pop();
    if (pathSegment) {
      return extractCleanFilename(pathSegment);
    }
  } catch {
    // Fall back to direct string extraction
  }
  return extractCleanFilename(trimmedLabel || href);
}
