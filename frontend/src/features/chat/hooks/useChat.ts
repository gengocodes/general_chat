"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { authService } from "@/features/auth/services/auth.service";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { LoginRequiredApiError } from "@/shared/api/stream";
import {
  STREAM_FALLBACK_ERROR_MESSAGE,
  UNEXPECTED_STREAM_ERROR_MESSAGE,
} from "../constants/chat.constants";
import { chatService } from "../services/chat.service";
import {
  AttachedFileItem,
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
    removeMessagesByIds,
    appendMessageContent,
    updateMessageActivity,
    setExecutionTime,
    finalizeMessageActivities,
    addAttachedFile,
    removeAttachedFile,
    clearAttachedFiles,
  } = useChatStore();

  const { setSession, setRequiresLogin, setPendingSubmission } = useAuthStore();

  const [isSending, setIsSending] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const syncGuestSessionAfterStream = useCallback(async () => {
    const { user, requiresLogin } = useAuthStore.getState();
    if (user !== null || requiresLogin) return;
    try {
      const session = await authService.getSession();
      setSession(session.user, session.login_required);
    } catch {
      // Non-fatal: the backend still enforces the quota on the next request.
    }
  }, [setSession]);

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

  const dispatchMessage = useCallback(
    async (content: string, filesToAttach: readonly AttachedFileItem[]) => {
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

      const currentFiles = [...filesToAttach];
      const currentObjectKeys = currentFiles.map((f) => f.objectKey);

      const userMsgId = `user-${Date.now()}`;
      const userMsg: ChatMessageItem = {
        id: userMsgId,
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
          appendMessageContent(assistantMsgId, STREAM_FALLBACK_ERROR_MESSAGE);
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
                finishStream(event.error || UNEXPECTED_STREAM_ERROR_MESSAGE);
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

        if (err instanceof LoginRequiredApiError) {
          removeMessagesByIds([userMsgId, assistantMsgId]);
          setPendingSubmission({
            message: trimmed,
            attachedFiles: currentFiles,
          });
          setRequiresLogin(true);
          setIsSending(false);
          return;
        }

        const errorMessage =
          err instanceof Error ? err.message : UNEXPECTED_STREAM_ERROR_MESSAGE;
        finishStream(errorMessage);
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
          setIsSending(false);
        }
        await syncGuestSessionAfterStream();
      }
    },
    [
      addMessage,
      appendMessageContent,
      cancelStream,
      clearAttachedFiles,
      finalizeMessageActivities,
      isSending,
      messages,
      removeMessagesByIds,
      setExecutionTime,
      setPendingSubmission,
      setRequiresLogin,
      syncGuestSessionAfterStream,
      updateMessageActivity,
    ],
  );

  const sendMessage = useCallback(
    async (content: string) => {
      await dispatchMessage(content, attachedFiles);
    },
    [attachedFiles, dispatchMessage],
  );

  const retryPendingSubmission = useCallback(async () => {
    const pending = useAuthStore.getState().pendingSubmission;
    if (!pending) return;
    setPendingSubmission(null);
    await dispatchMessage(pending.message, pending.attachedFiles);
  }, [dispatchMessage, setPendingSubmission]);

  return {
    messages,
    attachedFiles,
    sendMessage,
    retryPendingSubmission,
    cancelStream,
    addAttachedFile,
    removeAttachedFile,
    isSending,
  };
};
