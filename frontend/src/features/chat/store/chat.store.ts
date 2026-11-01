import { create } from "zustand";
import {
  AgentActivity,
  AttachedFileItem,
  ChatMessageItem,
  ChatStoreState,
} from "../types/chat.types";

export const useChatStore = create<ChatStoreState>((set) => ({
  messages: [],
  attachedFiles: [],

  addMessage: (msg: ChatMessageItem) =>
    set((state) => ({
      messages: [...state.messages, msg],
    })),

  removeMessagesByIds: (ids: string[]) =>
    set((state) => ({
      messages: state.messages.filter((msg) => !ids.includes(msg.id)),
    })),

  appendMessageContent: (id: string, chunk: string) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content: msg.content + chunk } : msg,
      ),
    })),

  updateMessageActivity: (msgId: string, activity: AgentActivity) =>
    set((state) => ({
      messages: state.messages.map((msg) => {
        if (msg.id !== msgId) return msg;
        const currentActivities = msg.activities || [];
        const existsIndex = currentActivities.findIndex(
          (a) => a.id === activity.id,
        );
        let updatedActivities: AgentActivity[];

        if (existsIndex >= 0) {
          updatedActivities = [...currentActivities];
          updatedActivities[existsIndex] = activity;
        } else {
          updatedActivities = [...currentActivities, activity];
        }

        return { ...msg, activities: updatedActivities };
      }),
    })),

  setExecutionTime: (msgId: string, durationSeconds: number) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === msgId
          ? { ...msg, executionTimeSeconds: durationSeconds }
          : msg,
      ),
    })),

  finalizeMessageActivities: (msgId: string) =>
    set((state) => ({
      messages: state.messages.map((msg) => {
        if (msg.id !== msgId) return msg;
        const completedActivities = (msg.activities || []).filter(
          (a) => a.status === "completed",
        );
        return {
          ...msg,
          activities:
            completedActivities.length > 0 ? completedActivities : undefined,
        };
      }),
    })),

  addAttachedFile: (file: AttachedFileItem) =>
    set((state) => ({
      attachedFiles: [...state.attachedFiles, file],
    })),

  removeAttachedFile: (objectKey: string) =>
    set((state) => ({
      attachedFiles: state.attachedFiles.filter(
        (f) => f.objectKey !== objectKey,
      ),
    })),

  clearAttachedFiles: () =>
    set({
      attachedFiles: [],
    }),
}));
