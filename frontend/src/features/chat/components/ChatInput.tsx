"use client";

import React, {
  useState,
  KeyboardEvent,
  useRef,
  useEffect,
  ChangeEvent,
} from "react";
import { ArrowUp, Square, Paperclip, Clock } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { FileAttachmentCard } from "@/shared/ui/file-card";
import { chatService } from "../services/chat.service";
import { AttachedFileItem } from "../types/chat.types";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onSend: (message: string) => void;
  onCancel: () => void;
  isSending: boolean;
  attachedFiles: AttachedFileItem[];
  onAddFile: (file: AttachedFileItem) => void;
  onRemoveFile: (objectKey: string) => void;
  showDisclaimer?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  placeholder = "Ask Gengo",
  onSend,
  onCancel,
  isSending,
  attachedFiles,
  onAddFile,
  onRemoveFile,
  showDisclaimer = true,
}) => {
  const [uploadingFilename, setUploadingFilename] = useState<string | null>(
    null,
  );
  const [uploadError, setUploadError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isUploading = uploadingFilename !== null;

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200,
      )}px`;
    }
  }, [value]);

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingFilename(file.name);
    setUploadError(null);

    try {
      const data = await chatService.uploadFile(file);
      onAddFile({
        objectKey: data.filename,
        originalName: data.original_name,
        sizeBytes: data.size_bytes,
        downloadUrl: data.download_url,
      });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to upload file.";
      setUploadError(message);
    } finally {
      setUploadingFilename(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleSend = () => {
    if (
      (!value.trim() && attachedFiles.length === 0) ||
      isSending ||
      isUploading
    ) {
      return;
    }
    setUploadError(null);
    onSend(value || "Please analyze or convert the attached file.");
    onChange("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasTrayItems = attachedFiles.length > 0 || uploadingFilename !== null;

  return (
    <div className="w-full flex flex-col gap-2">
      {uploadError && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 px-3.5 py-2 text-xs text-destructive">
          {uploadError}
        </div>
      )}

      <div className="relative flex flex-col rounded-3xl border border-border bg-card shadow-sm transition-all focus-within:border-foreground/25 focus-within:shadow-md">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept=".pdf,.docx,.doc,.txt,.md,.csv,.json"
          className="hidden"
        />

        {hasTrayItems && (
          <div className="flex flex-col gap-2 border-b border-border/60 bg-secondary/35 px-3.5 pt-3 pb-2.5 rounded-t-3xl">
            <div className="flex flex-wrap gap-2.5">
              {attachedFiles.map((file) => (
                <FileAttachmentCard
                  key={file.objectKey}
                  filename={file.objectKey}
                  originalName={file.originalName}
                  sizeBytes={file.sizeBytes}
                  onRemove={() => onRemoveFile(file.objectKey)}
                />
              ))}

              {uploadingFilename && (
                <FileAttachmentCard
                  filename={uploadingFilename}
                  originalName={uploadingFilename}
                  isUploading
                />
              )}
            </div>

            <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <Clock className="size-3 text-foreground/70 shrink-0" />
              <span>
                Uploaded and converted files are automatically deleted after 24
                hours.
              </span>
            </div>
          </div>
        )}

        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          className="w-full min-h-[56px] max-h-48 resize-none border-0 bg-transparent px-4 pt-3.5 pb-1.5 text-[15px] leading-relaxed text-foreground placeholder:text-muted-foreground/65 outline-none focus:outline-none focus:ring-0"
        />

        <div className="flex items-center justify-between px-3 pb-2.5 pt-1">
          <div className="flex items-center gap-1.5">
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => fileInputRef.current?.click()}
              disabled={isSending || isUploading}
              title="Attach document (max 10 MB)"
              className="h-8 rounded-xl px-2.5 text-xs font-medium text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors cursor-pointer gap-1.5"
            >
              <Paperclip className="size-3.5" />
              <span>Attach</span>
            </Button>
          </div>

          <div className="flex items-center gap-2">
            {isSending ? (
              <Button
                type="button"
                size="icon"
                onClick={onCancel}
                title="Stop generating"
                className="size-8 rounded-xl bg-foreground text-background hover:bg-foreground/90 transition-all cursor-pointer"
              >
                <Square className="size-3.5 fill-current" />
              </Button>
            ) : (
              <Button
                type="button"
                size="icon"
                onClick={handleSend}
                disabled={
                  (!value.trim() && attachedFiles.length === 0) || isUploading
                }
                title="Send message"
                className="size-8 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-30 disabled:bg-muted disabled:text-muted-foreground transition-all cursor-pointer shadow-2xs"
              >
                <ArrowUp className="size-4 stroke-[2.25]" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {showDisclaimer && (
        <p className="text-center text-[11px] text-muted-foreground/70 select-none px-2">
          Gengo can make mistakes. Uploaded &amp; converted files expire
          automatically after 24 hours.
        </p>
      )}
    </div>
  );
};
