import { create } from "zustand";
import {
  AuthStoreState,
  AuthUser,
  PendingChatSubmission,
} from "../types/auth.types";

export const useAuthStore = create<AuthStoreState>((set) => ({
  user: null,
  requiresLogin: false,
  isGoogleLoggingIn: false,
  authError: null,
  pendingSubmission: null,

  setSession: (user: AuthUser | null, requiresLogin: boolean) =>
    set({
      user,
      requiresLogin,
      authError: null,
    }),

  setRequiresLogin: (requiresLogin: boolean) =>
    set({
      requiresLogin,
    }),

  setIsGoogleLoggingIn: (isGoogleLoggingIn: boolean) =>
    set({
      isGoogleLoggingIn,
    }),

  setAuthError: (authError: string | null) =>
    set({
      authError,
    }),

  setPendingSubmission: (pendingSubmission: PendingChatSubmission | null) =>
    set({
      pendingSubmission,
    }),
}));
