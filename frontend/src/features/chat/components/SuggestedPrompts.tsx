"use client";

import React from "react";
import {
  Sparkles,
  Zap,
  Calculator,
  Lightbulb,
  Clock,
  Plus,
  Settings,
  BarChart3,
  ArrowUpRight,
  Code,
} from "lucide-react";
import { SUGGESTED_PROMPTS } from "../constants/chat.constants";
import { cn } from "@/lib/utils";

interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

export const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({
  onSelectPrompt,
  disabled,
}) => {
  const getPromptIcon = (iconName: string) => {
    switch (iconName) {
      case "zap":
        return <Zap className="size-4 text-amber-500 shrink-0" />;
      case "calculator":
        return <Calculator className="size-4 text-blue-500 shrink-0" />;
      case "lightbulb":
        return <Lightbulb className="size-4 text-emerald-500 shrink-0" />;
      case "clock":
        return <Clock className="size-4 text-purple-500 shrink-0" />;
      case "plus":
        return <Plus className="size-4 text-teal-500 shrink-0" />;
      case "settings":
        return <Settings className="size-4 text-slate-500 shrink-0" />;
      case "chart":
        return <BarChart3 className="size-4 text-indigo-500 shrink-0" />;
      case "code":
        return <Code className="size-4 text-sky-500 shrink-0" />;
      default:
        return <Sparkles className="size-4 text-primary shrink-0" />;
    }
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-2 gap-2 sm:gap-3.5 w-full mt-4 sm:mt-8 text-left">
      {SUGGESTED_PROMPTS.map((promptItem) => (
        <button
          key={promptItem.title}
          type="button"
          onClick={() => onSelectPrompt(promptItem.prompt)}
          disabled={disabled}
          className={cn(
            "group relative flex flex-col justify-between p-3 sm:p-4 rounded-xl sm:rounded-2xl border border-border/50 bg-card/60 hover:bg-muted/50 hover:border-border/80 transition-all duration-200 cursor-pointer text-left select-none shadow-2xs hover:shadow-sm active:scale-[0.98]",
            disabled && "opacity-50 cursor-not-allowed",
          )}
        >
          <div className="flex items-center justify-between w-full sm:mb-1">
            <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
              {getPromptIcon(promptItem.icon)}
              <span className="text-xs sm:text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                {promptItem.title}
              </span>
            </div>
            <ArrowUpRight className="size-3.5 text-muted-foreground/40 group-hover:text-primary group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all shrink-0 hidden sm:block" />
          </div>
          <p className="text-xs text-muted-foreground/70 line-clamp-2 leading-relaxed hidden sm:block">
            {promptItem.desc}
          </p>
        </button>
      ))}
    </div>
  );
};
