"use client";

import React from "react";
import { GoogleLogin } from "@react-oauth/google";
import { GOOGLE_SIGN_IN_ERROR_MESSAGE } from "../constants/auth.constants";
import { useAuth } from "../hooks/useAuth";
import { GoogleSignInButtonProps } from "../types/auth.types";

export const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onSignedIn,
}) => {
  const { googleLogin, isGoogleLoggingIn, setAuthError } = useAuth();

  return (
    <div
      className={
        isGoogleLoggingIn
          ? "opacity-60 pointer-events-none inline-flex"
          : "inline-flex"
      }
    >
      <GoogleLogin
        onSuccess={async (response) => {
          if (!response.credential) {
            setAuthError(GOOGLE_SIGN_IN_ERROR_MESSAGE);
            return;
          }
          const ok = await googleLogin(response.credential);
          if (ok) {
            onSignedIn();
          }
        }}
        onError={() => {
          setAuthError(GOOGLE_SIGN_IN_ERROR_MESSAGE);
        }}
        useOneTap={false}
        theme="outline"
        size="large"
        shape="pill"
        text="continue_with"
      />
    </div>
  );
};
