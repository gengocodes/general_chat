import { create } from "zustand";
import {
  AgentActivity,
  AgentToolCall,
  ChatMessageItem,
} from "../types/chat.types";

interface ChatState {
  messages: ChatMessageItem[];
  attachedFiles: string[];
  addMessage: (msg: ChatMessageItem) => void;
  appendMessageContent: (id: string, chunk: string) => void;
  updateMessageActivity: (msgId: string, activity: AgentActivity) => void;
  updateMessageToolCall: (
    msgId: string,
    toolName: string,
    status: "started" | "completed",
  ) => void;
  setExecutionTime: (msgId: string, durationSeconds: number) => void;
  finalizeMessageActivities: (msgId: string) => void;
  resetMessages: () => void;
  addAttachedFile: (filename: string) => void;
  removeAttachedFile: (filename: string) => void;
  clearAttachedFiles: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  attachedFiles: [],

  addMessage: (msg: ChatMessageItem) =>
    set((state) => ({
      messages: [...state.messages, msg],
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

  updateMessageToolCall: (
    msgId: string,
    toolName: string,
    status: "started" | "completed",
  ) =>
    set((state) => ({
      messages: state.messages.map((msg) => {
        if (msg.id !== msgId) return msg;
        const currentTools = msg.tools || [];
        const existsIndex = currentTools.findIndex((t) => t.name === toolName);
        let updatedTools: AgentToolCall[];

        const toolCall: AgentToolCall = {
          id: `tool-${toolName}`,
          name: toolName,
          label: toolName.replace(/_/g, " "),
          status,
        };

        if (existsIndex >= 0) {
          updatedTools = [...currentTools];
          updatedTools[existsIndex] = toolCall;
        } else {
          updatedTools = [...currentTools, toolCall];
        }

        return { ...msg, tools: updatedTools };
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
        const completedTools = (msg.tools || []).filter(
          (t) => t.status === "completed",
        );
        return {
          ...msg,
          activities:
            completedActivities.length > 0 ? completedActivities : undefined,
          tools: completedTools.length > 0 ? completedTools : undefined,
        };
      }),
    })),

  resetMessages: () =>
    set({
      messages: [],
      attachedFiles: [],
    }),

  addAttachedFile: (filename: string) =>
    set((state) => ({
      attachedFiles: [...state.attachedFiles, filename],
    })),

  removeAttachedFile: (filename: string) =>
    set((state) => ({
      attachedFiles: state.attachedFiles.filter((f) => f !== filename),
    })),

  clearAttachedFiles: () =>
    set({
      attachedFiles: [],
    }),
}));
