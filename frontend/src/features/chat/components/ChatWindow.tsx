"use client";

import React, { useRef, useEffect } from "react";
import { Sparkles } from "lucide-react";
import { useChat } from "../hooks/useChat";
import { DEFAULT_PROMPTS } from "../constants/chat.constants";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

export const ChatWindow: React.FC = () => {
  const {
    messages,
    attachedFiles,
    sendMessage,
    cancelStream,
    isSending,
    addAttachedFile,
    removeAttachedFile,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  return (
    <div className="flex flex-col h-full w-full bg-background overflow-hidden relative">
      <div className="flex-1 overflow-y-auto w-full px-3 md:px-6 py-4 md:py-6 scroll-smooth flex flex-col">
        <div className="max-w-3xl md:max-w-4xl mx-auto w-full space-y-6 flex-1 flex flex-col">
          {messages.map((msg) => {
            const hasData =
              Boolean(msg.content) ||
              Boolean(msg.activities && msg.activities.length > 0);

            return msg.role === "assistant" && !hasData ? null : (
              <ChatMessage key={msg.id} message={msg} />
            );
          })}

          {messages.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center text-center animate-in fade-in-50 duration-500 max-w-3xl mx-auto px-1 py-4 sm:py-8 my-auto">
              <div className="p-3 bg-primary/10 rounded-2xl mb-4 border border-primary/20 text-primary">
                <Sparkles className="size-8" />
              </div>

              <h1 className="text-2xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground leading-[1.15] max-w-2xl">
                Chat with <span className="text-primary">GenChat</span>
              </h1>

              <p className="text-xs sm:text-base text-muted-foreground mt-2 sm:mt-3.5 max-w-lg leading-relaxed font-normal">
                Paul Corsino&apos;s intelligent AI assistant. Ask questions,
                brainstorm ideas, analyze data, or build next-gen solutions.
              </p>

              <div className="flex flex-wrap gap-2 justify-center mt-6 max-w-xl">
                {DEFAULT_PROMPTS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => sendMessage(p)}
                    disabled={isSending}
                    className="text-xs px-3.5 py-2 rounded-full border border-border bg-card hover:bg-muted text-foreground transition-all cursor-pointer inline-flex items-center gap-1.5"
                  >
                    <Sparkles className="size-3 text-muted-foreground" />
                    <span>{p}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <footer className="w-full px-3 md:px-6 pt-2 pb-4 shrink-0">
        <div className="max-w-3xl md:max-w-4xl mx-auto w-full">
          <ChatInput
            onSend={sendMessage}
            onCancel={cancelStream}
            isSending={isSending}
            attachedFiles={attachedFiles}
            onAddFile={addAttachedFile}
            onRemoveFile={removeAttachedFile}
          />
        </div>
      </footer>
    </div>
  );
};
