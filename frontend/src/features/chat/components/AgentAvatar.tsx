"use client";

import React from "react";
import { BotMessageSquare } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface AgentAvatarProps {
  className?: string;
}

export const AgentAvatar: React.FC<AgentAvatarProps> = ({ className }) => (
  <div
    className={cn(
      "bg-primary text-primary-foreground flex items-center justify-center transition-transform hover:scale-105 shrink-0 h-8 w-8 md:h-9 md:w-9 rounded-xl shadow-2xs",
      className,
    )}
  >
    <BotMessageSquare className="h-4 w-4" />
  </div>
);
