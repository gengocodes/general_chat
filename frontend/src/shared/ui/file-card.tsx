"use client";

import React from "react";
import { Icon, IconifyIcon } from "@iconify/react";
import pdfIcon from "@iconify-icons/vscode-icons/file-type-pdf2";
import wordIcon from "@iconify-icons/vscode-icons/file-type-word";
import { Download, File, X } from "lucide-react";
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
  sm: "size-8",
  md: "size-10",
  lg: "size-11",
};

const KIND_ICONS: Record<Exclude<FileKind, "generic">, IconifyIcon> = {
  pdf: pdfIcon,
  docx: wordIcon,
};

/**
 * File-type icon for PDF and Word documents (bundled offline vscode-icons set),
 * falling back to a neutral file glyph for any other type.
 */
export const FileTypeIcon: React.FC<FileTypeIconProps> = ({
  filename,
  size = "md",
  className,
}) => {
  const kind = getFileKind(filename);
  const classes = cn("shrink-0 select-none", SIZE_CLASSES[size], className);

  if (kind === "generic") {
    return (
      <File
        className={cn(classes, "p-1 text-muted-foreground")}
        strokeWidth={1.5}
        aria-hidden="true"
      />
    );
  }

  return <Icon icon={KIND_ICONS[kind]} className={classes} aria-hidden="true" />;
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
