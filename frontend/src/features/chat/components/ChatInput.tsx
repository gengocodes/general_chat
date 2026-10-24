"use client";

import React, {
  useState,
  KeyboardEvent,
  useRef,
  useEffect,
  ChangeEvent,
} from "react";
import { ArrowUp, Square, Paperclip, X, FileText } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { chatService } from "../services/chat.service";

interface ChatInputProps {
  onSend: (message: string) => void;
  onCancel: () => void;
  isSending: boolean;
  attachedFiles: string[];
  onAddFile: (filename: string) => void;
  onRemoveFile: (filename: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  onCancel,
  isSending,
  attachedFiles,
  onAddFile,
  onRemoveFile,
}) => {
  const [input, setInput] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        180,
      )}px`;
    }
  }, [input]);

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      const data = await chatService.uploadFile(file);
      onAddFile(data.filename);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to upload file.";
      setUploadError(message);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleSend = () => {
    if ((!input.trim() && attachedFiles.length === 0) || isSending) return;
    setUploadError(null);
    onSend(input || "Analyze attached file.");
    setInput("");
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

  return (
    <div className="w-full flex flex-col gap-2">
      {uploadError && (
        <p className="text-xs text-destructive px-2">{uploadError}</p>
      )}

      {attachedFiles.length > 0 && (
        <div className="flex flex-col gap-1.5 px-1">
          <div className="flex flex-wrap gap-2">
            {attachedFiles.map((file) => (
              <div
                key={file}
                className="inline-flex items-center gap-1.5 text-xs bg-muted/80 border border-border px-2.5 py-1 rounded-full text-foreground"
              >
                <FileText className="size-3.5 text-primary" />
                <span className="font-medium max-w-[200px] truncate">{file}</span>
                <button
                  type="button"
                  onClick={() => onRemoveFile(file)}
                  className="text-muted-foreground hover:text-foreground ml-1"
                >
                  <X className="size-3" />
                </button>
              </div>
            ))}
          </div>
          <p className="text-xxs text-muted-foreground/70 px-1">
            Uploaded and converted files are automatically removed after 24 hours.
          </p>
        </div>
      )}

      <div className="relative flex items-end gap-2 border border-border/70 rounded-3xl md:rounded-[28px] bg-card p-2 md:p-2.5 shadow-md shadow-black/5 transition-all">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          className="hidden"
        />

        <Button
          type="button"
          size="icon"
          variant="ghost"
          onClick={() => fileInputRef.current?.click()}
          disabled={isSending || isUploading}
          title="Attach file"
          className="rounded-full shrink-0 h-8 w-8 md:h-9 md:w-9 text-muted-foreground hover:text-foreground transition-all cursor-pointer mb-0.5"
        >
          <Paperclip className="h-4 w-4" />
        </Button>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask GenChat anything..."
          rows={1}
          className="flex-1 min-h-10 max-h-40 resize-none border-0 outline-none focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0 text-base md:text-sm px-2 md:px-3 py-2 bg-transparent text-foreground placeholder:text-muted-foreground/60 leading-relaxed"
        />

        {isSending ? (
          <Button
            size="icon"
            variant="secondary"
            onClick={onCancel}
            title="Stop generating"
            className="rounded-full shrink-0 h-8 w-8 md:h-9 md:w-9 bg-foreground text-background hover:bg-foreground/90 transition-all cursor-pointer mb-0.5"
          >
            <Square className="h-3.5 w-3.5" />
          </Button>
        ) : (
          <Button
            size="icon"
            onClick={handleSend}
            disabled={
              (!input.trim() && attachedFiles.length === 0) || isUploading
            }
            title="Send message"
            className="rounded-full shrink-0 h-8 w-8 md:h-9 md:w-9 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-30 disabled:bg-muted disabled:text-muted-foreground transition-all cursor-pointer mb-0.5"
          >
            <ArrowUp className="h-4 w-4 stroke-[2.5]" />
          </Button>
        )}
      </div>

      <p className="text-center text-xs text-muted-foreground/60 select-none px-2">
        GenChat can make mistakes. Uploaded files are automatically deleted after 24 hours.
      </p>
    </div>
  );
};
