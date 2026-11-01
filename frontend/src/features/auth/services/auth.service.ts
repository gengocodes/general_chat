import { parseErrorResponse } from "@/shared/api/stream";
import {
  AUTH_GOOGLE_ENDPOINT,
  AUTH_LOGOUT_ENDPOINT,
  AUTH_LOGOUT_ERROR_MESSAGE,
  AUTH_SESSION_ENDPOINT,
  AUTH_SESSION_ERROR_MESSAGE,
  GOOGLE_SIGN_IN_ERROR_MESSAGE,
} from "../constants/auth.constants";
import {
  AuthServiceContract,
  AuthUser,
  SessionResponse,
} from "../types/auth.types";

export const authService: AuthServiceContract = {
  async getSession(): Promise<SessionResponse> {
    const response = await fetch(AUTH_SESSION_ENDPOINT, {
      method: "GET",
      credentials: "include",
    });

    if (!response.ok) {
      throw await parseErrorResponse(response, AUTH_SESSION_ERROR_MESSAGE);
    }

    return (await response.json()) as SessionResponse;
  },

  async googleLogin(credential: string): Promise<AuthUser> {
    const response = await fetch(AUTH_GOOGLE_ENDPOINT, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ credential }),
    });

    if (!response.ok) {
      throw await parseErrorResponse(response, GOOGLE_SIGN_IN_ERROR_MESSAGE);
    }

    return (await response.json()) as AuthUser;
  },

  async logout(): Promise<void> {
    const response = await fetch(AUTH_LOGOUT_ENDPOINT, {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) {
      throw await parseErrorResponse(response, AUTH_LOGOUT_ERROR_MESSAGE);
    }
  },
};
