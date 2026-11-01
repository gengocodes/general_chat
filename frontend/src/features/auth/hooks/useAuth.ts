"use client";

import { useCallback } from "react";
import {
  AUTH_LOGOUT_ERROR_MESSAGE,
  GOOGLE_SIGN_IN_ERROR_MESSAGE,
} from "../constants/auth.constants";
import { authService } from "../services/auth.service";
import { useAuthStore } from "../store/auth.store";

export const useAuth = () => {
  const {
    user,
    requiresLogin,
    isGoogleLoggingIn,
    authError,
    pendingSubmission,
    setSession,
    setRequiresLogin,
    setIsGoogleLoggingIn,
    setAuthError,
    setPendingSubmission,
  } = useAuthStore();

  const refreshSession = useCallback(async () => {
    try {
      const session = await authService.getSession();
      setSession(session.user, session.login_required);
    } catch {
      // Non-fatal: session check failure should not block rendering.
    }
  }, [setSession]);

  const googleLogin = useCallback(
    async (credential: string): Promise<boolean> => {
      setIsGoogleLoggingIn(true);
      setAuthError(null);
      try {
        const signedInUser = await authService.googleLogin(credential);
        setSession(signedInUser, false);
        return true;
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : GOOGLE_SIGN_IN_ERROR_MESSAGE;
        setAuthError(message);
        return false;
      } finally {
        setIsGoogleLoggingIn(false);
      }
    },
    [setAuthError, setIsGoogleLoggingIn, setSession],
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
      const session = await authService.getSession();
      setSession(session.user, session.login_required);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : AUTH_LOGOUT_ERROR_MESSAGE;
      setAuthError(message);
    }
  }, [setAuthError, setSession]);

  return {
    user,
    requiresLogin,
    isGoogleLoggingIn,
    authError,
    pendingSubmission,
    refreshSession,
    googleLogin,
    logout,
    setRequiresLogin,
    setAuthError,
    setPendingSubmission,
  };
};
