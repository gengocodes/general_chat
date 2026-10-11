"use client";

import React from "react";
import { User } from "lucide-react";
import { cn } from "@/lib/utils";

interface UserAvatarProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const UserAvatar: React.FC<UserAvatarProps> = ({
  size = "md",
  className,
}) => {
  const sizeClasses = {
    sm: "h-8 w-8 rounded-xl",
    md: "h-8 w-8 md:h-9 md:w-9 rounded-xl",
    lg: "h-14 w-14 rounded-2xl",
  };

  const iconSizeClasses = {
    sm: "h-4 w-4",
    md: "h-4 w-4",
    lg: "h-7 w-7",
  };

  return (
    <div
      className={cn(
        "flex items-center justify-center font-semibold text-xs shrink-0 shadow-2xs bg-muted text-foreground border border-border/60 transition-transform hover:scale-105",
        sizeClasses[size],
        className,
      )}
    >
      <User className={iconSizeClasses[size]} />
    </div>
  );
};
