"use client";

import React from "react";
import { User } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface UserAvatarProps {
  className?: string;
}

export const UserAvatar: React.FC<UserAvatarProps> = ({ className }) => (
  <div
    className={cn(
      "flex items-center justify-center font-semibold text-xs shrink-0 shadow-2xs bg-muted text-foreground border border-border/60 transition-transform hover:scale-105 h-8 w-8 md:h-9 md:w-9 rounded-xl",
      className,
    )}
  >
    <User className="h-4 w-4" />
  </div>
);
