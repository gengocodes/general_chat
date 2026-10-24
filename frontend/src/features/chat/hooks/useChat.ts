"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { chatService } from "../services/chat.service";
import {
  ChatMessageItem,
  AgentStreamEvent,
  ChatHistoryMessage,
} from "../types/chat.types";
import { useChatStore } from "../store/chat.store";

export const useChat = () => {
  const {
    messages,
    attachedFiles,
    addMessage,
    appendMessageContent,
    updateMessageActivity,
    setExecutionTime,
    finalizeMessageActivities,
    addAttachedFile,
    removeAttachedFile,
    clearAttachedFiles,
  } = useChatStore();

  const [isSending, setIsSending] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsSending(false);
  }, []);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const sendMessage = async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed || isSending) return;

    cancelStream();

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const startTime = Date.now();
    setIsSending(true);

    const historyPayload: ChatHistoryMessage[] = messages
      .filter((msg) => msg.content.trim().length > 0)
      .map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

    const currentFiles = [...attachedFiles];
    const currentObjectKeys = currentFiles.map((f) => f.objectKey);

    const userMsg: ChatMessageItem = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
      attachedFiles: currentFiles.length > 0 ? currentFiles : undefined,
      createdAt: new Date(),
    };

    const assistantMsgId = `assistant-${Date.now()}`;
    const assistantMsg: ChatMessageItem = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      createdAt: new Date(),
    };

    addMessage(userMsg);
    addMessage(assistantMsg);
    clearAttachedFiles();

    let hasReceivedTokens = false;

    const finishStream = (errText?: string) => {
      const durationSeconds = Number(
        ((Date.now() - startTime) / 1000).toFixed(1),
      );
      setExecutionTime(assistantMsgId, durationSeconds);
      finalizeMessageActivities(assistantMsgId);

      if (errText && !hasReceivedTokens) {
        appendMessageContent(
          assistantMsgId,
          "Sorry, I encountered an error generating a response. Please try again.",
        );
      }
      setIsSending(false);
    };

    try {
      await chatService.streamMessage(
        {
          message: trimmed,
          history: historyPayload,
          attached_files: currentObjectKeys,
        },
        (event: AgentStreamEvent) => {
          if (controller.signal.aborted) return;

          switch (event.type) {
            case "activity":
              updateMessageActivity(assistantMsgId, {
                id: event.id,
                message: event.message,
                status: event.status,
              });
              break;

            case "token":
              hasReceivedTokens = true;
              appendMessageContent(assistantMsgId, event.token);
              break;

            case "error":
              finishStream(event.error || "An unexpected error occurred.");
              break;

            case "complete":
              finishStream();
              break;
          }
        },
        controller.signal,
      );
    } catch (err: unknown) {
      if (controller.signal.aborted) return;

      const errorMessage =
        err instanceof Error ? err.message : "An unexpected error occurred.";
      finishStream(errorMessage);
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
        setIsSending(false);
      }
    }
  };

  return {
    messages,
    attachedFiles,
    sendMessage,
    cancelStream,
    addAttachedFile,
    removeAttachedFile,
    isSending,
  };
};
