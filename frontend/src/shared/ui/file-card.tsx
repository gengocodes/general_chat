"use client";

import React from "react";
import { Download, X } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import {
  FileKind,
  extractCleanFilename,
  formatFileSize,
  getFileExtension,
  getFileKind,
} from "@/shared/lib/file-utils";
import { Spinner } from "@/shared/ui/spinner";

interface FileTypeIconProps {
  filename: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZE_CLASSES: Record<NonNullable<FileTypeIconProps["size"]>, string> = {
  sm: "size-8 rounded-lg",
  md: "size-10 rounded-xl",
  lg: "size-11 rounded-xl",
};

const KIND_STYLES: Record<
  FileKind,
  { bg: string; border: string; text: string; badgeBg: string }
> = {
  pdf: {
    bg: "bg-red-500/10 dark:bg-red-500/15",
    border: "border-red-500/25 dark:border-red-400/25",
    text: "text-red-600 dark:text-red-400",
    badgeBg: "bg-red-600 dark:bg-red-500 text-white",
  },
  docx: {
    bg: "bg-blue-500/10 dark:bg-blue-500/15",
    border: "border-blue-500/25 dark:border-blue-400/25",
    text: "text-blue-600 dark:text-blue-400",
    badgeBg: "bg-blue-600 dark:bg-blue-500 text-white",
  },
  generic: {
    bg: "bg-muted",
    border: "border-border",
    text: "text-foreground",
    badgeBg: "bg-foreground text-background",
  },
};

/**
 * Vector document emblem with folded corner and color-coded format badge (PDF in red, DOCX in blue).
 */
export const FileTypeIcon: React.FC<FileTypeIconProps> = ({
  filename,
  size = "md",
  className,
}) => {
  const kind = getFileKind(filename);
  const ext = getFileExtension(filename);
  const style = KIND_STYLES[kind];
  const badgeText =
    kind === "pdf" ? "PDF" : kind === "docx" ? "DOC" : ext.slice(0, 4);

  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center shrink-0 border select-none",
        SIZE_CLASSES[size],
        style.bg,
        style.border,
        style.text,
        className,
      )}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        className="size-4 opacity-85"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
      <span
        className={cn(
          "mt-0.5 px-1 py-[1px] rounded-[3px] text-[8px] font-bold tracking-wider leading-none uppercase",
          style.badgeBg,
        )}
      >
        {badgeText}
      </span>
    </div>
  );
};

export interface FileAttachmentCardProps {
  filename: string;
  originalName?: string;
  sizeBytes?: number;
  isUploading?: boolean;
  onRemove?: () => void;
  compact?: boolean;
  className?: string;
}

/**
 * File attachment card used in the composer attachment tray and user messages.
 */
export const FileAttachmentCard: React.FC<FileAttachmentCardProps> = ({
  filename,
  originalName,
  sizeBytes,
  isUploading = false,
  onRemove,
  compact = false,
  className,
}) => {
  const displayName = extractCleanFilename(originalName || filename);
  const ext = getFileExtension(displayName);
  const sizeLabel =
    sizeBytes !== undefined && sizeBytes > 0 ? formatFileSize(sizeBytes) : null;

  return (
    <div
      className={cn(
        "group/file relative inline-flex items-center gap-2.5 rounded-xl border border-border bg-card px-2.5 py-2 text-left shadow-2xs transition-all hover:border-foreground/25",
        compact ? "max-w-[220px]" : "max-w-[260px]",
        className,
      )}
    >
      {isUploading ? (
        <div className="size-8 rounded-lg bg-muted flex items-center justify-center shrink-0">
          <Spinner className="size-4 text-foreground" />
        </div>
      ) : (
        <FileTypeIcon filename={displayName} size="sm" />
      )}

      <div className="min-w-0 flex-1 pr-1">
        <p
          className="truncate text-xs font-medium text-foreground leading-tight"
          title={displayName}
        >
          {displayName}
        </p>
        <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
          {isUploading
            ? "Uploading..."
            : sizeLabel
              ? `${ext} • ${sizeLabel}`
              : `${ext} Document`}
        </p>
      </div>

      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${displayName}`}
          className="-top-1.5 -right-1.5 absolute flex size-5 items-center justify-center rounded-full border border-border bg-background text-muted-foreground shadow-xs transition-all opacity-90 hover:opacity-100 hover:text-foreground hover:bg-muted cursor-pointer"
        >
          <X className="size-3" />
        </button>
      )}
    </div>
  );
};

export interface GeneratedFileCardProps {
  href: string;
  filename: string;
  className?: string;
}

/**
 * Generated artifact download card rendered when the assistant produces a converted PDF or DOCX.
 */
export const GeneratedFileCard: React.FC<GeneratedFileCardProps> = ({
  href,
  filename,
  className,
}) => {
  const cleanName = extractCleanFilename(filename);
  const ext = getFileExtension(cleanName);
  const kind = getFileKind(cleanName);
  const formatDescription =
    kind === "pdf"
      ? "Converted PDF Document"
      : kind === "docx"
        ? "Converted Word Document"
        : `Generated ${ext} File`;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      download={cleanName}
      className={cn(
        "group/dl my-2.5 flex items-center justify-between gap-3 rounded-2xl border border-border bg-card p-3 sm:p-3.5 text-left shadow-2xs transition-all hover:border-foreground/30 hover:bg-muted/30 no-underline",
        className,
      )}
    >
      <div className="flex items-center gap-3 min-w-0">
        <FileTypeIcon filename={cleanName} size="lg" />
        <div className="min-w-0 flex flex-col">
          <span className="truncate text-sm font-semibold text-foreground">
            {cleanName}
          </span>
          <span className="text-xs text-muted-foreground mt-0.5">
            {formatDescription} • Auto-deletes in 24h
          </span>
        </div>
      </div>

      <span className="inline-flex items-center gap-1.5 rounded-xl bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground shadow-2xs transition-opacity group-hover/dl:opacity-90 shrink-0">
        <Download className="size-3.5" />
        <span>Download</span>
      </span>
    </a>
  );
};
