"use client";

import React from "react";
import { LogOut } from "lucide-react";
import {
  SIGN_OUT_BUTTON_TITLE,
  SIGN_OUT_LABEL,
} from "../constants/auth.constants";
import { useAuth } from "../hooks/useAuth";

export const UserSessionBadge: React.FC = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card/90 backdrop-blur-xs pl-3 pr-1.5 py-1 shadow-2xs">
      <span
        className="text-xs font-medium text-foreground truncate max-w-40 sm:max-w-56"
        title={user.email}
      >
        {user.name}
      </span>

      <button
        type="button"
        onClick={() => void logout()}
        title={SIGN_OUT_BUTTON_TITLE}
        className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
      >
        <LogOut className="size-3" />
        <span>{SIGN_OUT_LABEL}</span>
      </button>
    </div>
  );
};
