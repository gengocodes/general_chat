"use client";

import React from "react";
import { cn } from "@/shared/lib/utils";
import { GengoLogo } from "@/shared/ui/gengo-logo";

interface AgentAvatarProps {
  className?: string;
}

export const AgentAvatar: React.FC<AgentAvatarProps> = ({ className }) => (
  <div
    className={cn(
      "flex items-center justify-center transition-transform hover:scale-105 shrink-0 h-8 w-8 md:h-9 md:w-9 rounded-full shadow-2xs",
      className,
    )}
  >
    <GengoLogo className="h-full w-full" />
  </div>
);
