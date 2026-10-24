"use client";

import React, { useState, useRef, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { PromptCategorySelector } from "./PromptCategorySelector";

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

  const [inputValue, setInputValue] = useState("");
  const [hoveredPrompt, setHoveredPrompt] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const isEmptyState = messages.length === 0;

  if (isEmptyState) {
    return (
      <div className="flex flex-col h-full w-full bg-background overflow-y-auto px-4 sm:px-6 py-8">
        <div className="flex-1 flex flex-col items-center justify-center w-full max-w-2xl mx-auto my-auto animate-in fade-in-50 duration-300">
          <div className="text-center mb-7">
            <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-foreground">
              Chat with Gengo
            </h1>
            <p className="text-sm text-muted-foreground mt-2">
              Paul Corsino&apos;s AI assistant. How can I help you today?
            </p>
          </div>

          <div className="w-full">
            <ChatInput
              value={inputValue}
              onChange={setInputValue}
              placeholder={hoveredPrompt || "Ask Gengo"}
              onSend={sendMessage}
              onCancel={cancelStream}
              isSending={isSending}
              attachedFiles={attachedFiles}
              onAddFile={addAttachedFile}
              onRemoveFile={removeAttachedFile}
              showDisclaimer={false}
            />

            <PromptCategorySelector
              onHoverPrompt={setHoveredPrompt}
              onSelectPrompt={(prompt) => setInputValue(prompt)}
            />
          </div>
        </div>

        <footer className="w-full pt-4 text-center shrink-0">
          <p className="text-[11px] text-muted-foreground/65 select-none">
            Gengo can make mistakes. Uploaded &amp; converted files expire
            automatically after 24 hours.
          </p>
        </footer>
      </div>
    );
  }

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

          <div ref={messagesEndRef} />
        </div>
      </div>

      <footer className="w-full px-3 md:px-6 pt-2 pb-4 shrink-0">
        <div className="max-w-3xl md:max-w-4xl mx-auto w-full">
          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            placeholder="Ask Gengo"
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
