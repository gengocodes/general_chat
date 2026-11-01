"use client";

import React from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { requireEnvValue } from "@/shared/lib/utils";
import { MISSING_GOOGLE_CLIENT_ID_ERROR } from "../constants/auth.constants";
import { AuthProviderProps } from "../types/auth.types";

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const clientId = requireEnvValue(
    process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
    MISSING_GOOGLE_CLIENT_ID_ERROR,
  );

  return (
    <GoogleOAuthProvider clientId={clientId}>
      {children}
    </GoogleOAuthProvider>
  );
};
