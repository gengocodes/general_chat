"use client";

import React from "react";
import { BotMessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentAvatarProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const AgentAvatar: React.FC<AgentAvatarProps> = ({
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
        "bg-linear-to-br from-primary to-sidebar-primary flex items-center justify-center text-white transition-transform hover:scale-105 shrink-0",
        sizeClasses[size],
        className,
      )}
    >
      <BotMessageSquare className={iconSizeClasses[size]} />
    </div>
  );
};
