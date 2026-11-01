import type { ReactNode } from "react";
import type { AttachedFileItem } from "@/features/chat/types/chat.types";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
}

export interface SessionResponse {
  user: AuthUser | null;
  login_required: boolean;
}

export interface PendingChatSubmission {
  message: string;
  attachedFiles: AttachedFileItem[];
}

export interface AuthServiceContract {
  getSession(): Promise<SessionResponse>;
  googleLogin(credential: string): Promise<AuthUser>;
  logout(): Promise<void>;
}

export interface AuthStoreState {
  user: AuthUser | null;
  requiresLogin: boolean;
  isGoogleLoggingIn: boolean;
  authError: string | null;
  pendingSubmission: PendingChatSubmission | null;
  setSession: (user: AuthUser | null, requiresLogin: boolean) => void;
  setRequiresLogin: (requiresLogin: boolean) => void;
  setIsGoogleLoggingIn: (isGoogleLoggingIn: boolean) => void;
  setAuthError: (error: string | null) => void;
  setPendingSubmission: (submission: PendingChatSubmission | null) => void;
}

export interface AuthProviderProps {
  children: ReactNode;
}

export interface GoogleSignInButtonProps {
  onSignedIn: () => void;
}

export interface LoginRequiredNoticeProps {
  onSignedIn: () => void;
}
