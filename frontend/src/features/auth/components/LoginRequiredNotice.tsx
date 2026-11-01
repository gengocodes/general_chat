"use client";

import React from "react";
import { Lock } from "lucide-react";
import {
  LOGIN_REQUIRED_DESCRIPTION,
  LOGIN_REQUIRED_HEADING,
} from "../constants/auth.constants";
import { useAuth } from "../hooks/useAuth";
import { LoginRequiredNoticeProps } from "../types/auth.types";
import { GoogleSignInButton } from "./GoogleSignInButton";

export const LoginRequiredNotice: React.FC<LoginRequiredNoticeProps> = ({
  onSignedIn,
}) => {
  const { authError } = useAuth();

  return (
    <div className="w-full rounded-2xl border border-border bg-card px-4 py-3.5 shadow-xs animate-in fade-in-50 slide-in-from-bottom-2 duration-200">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-xl border border-border bg-secondary text-foreground">
            <Lock className="size-3.5" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold tracking-tight text-foreground">
              {LOGIN_REQUIRED_HEADING}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
              {LOGIN_REQUIRED_DESCRIPTION}
            </p>
          </div>
        </div>

        <div className="shrink-0 flex items-center sm:justify-end">
          <GoogleSignInButton onSignedIn={onSignedIn} />
        </div>
      </div>

      {authError && (
        <p className="mt-2.5 text-xs text-destructive border-t border-border/60 pt-2">
          {authError}
        </p>
      )}
    </div>
  );
};
