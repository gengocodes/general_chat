"use client";

import React, { useState } from "react";
import {
  Sparkles,
  FileText,
  Code2,
  PenLine,
  Lightbulb,
  X,
  ChevronRight,
} from "lucide-react";
import { PROMPT_CATEGORIES } from "../constants/chat.constants";
import { PromptCategory, PromptCategoryIcon } from "../types/chat.types";

interface PromptCategorySelectorProps {
  onHoverPrompt: (prompt: string | null) => void;
  onSelectPrompt: (prompt: string) => void;
}

const CATEGORY_ICONS: Record<PromptCategoryIcon, React.ReactNode> = {
  sparkles: <Sparkles className="size-3.5 text-muted-foreground" />,
  files: <FileText className="size-3.5 text-muted-foreground" />,
  code: <Code2 className="size-3.5 text-muted-foreground" />,
  pen: <PenLine className="size-3.5 text-muted-foreground" />,
  lightbulb: <Lightbulb className="size-3.5 text-muted-foreground" />,
};

export const PromptCategorySelector: React.FC<PromptCategorySelectorProps> = ({
  onHoverPrompt,
  onSelectPrompt,
}) => {
  const [activeCategory, setActiveCategory] = useState<PromptCategory | null>(
    null,
  );

  const handleCloseCategory = () => {
    setActiveCategory(null);
    onHoverPrompt(null);
  };

  if (!activeCategory) {
    return (
      <div className="flex flex-wrap items-center justify-center gap-2 mt-4 animate-in fade-in-50 duration-200">
        {PROMPT_CATEGORIES.map((category) => (
          <button
            key={category.id}
            type="button"
            onClick={() => setActiveCategory(category)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-border/80 bg-card hover:bg-muted/70 px-3 py-1.5 text-xs font-medium text-foreground/90 shadow-2xs transition-all cursor-pointer"
          >
            {CATEGORY_ICONS[category.icon]}
            <span>{category.label}</span>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div
      className="w-full mt-3 rounded-2xl border border-border bg-card shadow-sm overflow-hidden animate-in fade-in-50 slide-in-from-top-1 duration-200"
      onMouseLeave={() => onHoverPrompt(null)}
    >
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/50">
        <div className="inline-flex items-center gap-2 text-xs font-medium text-muted-foreground">
          {CATEGORY_ICONS[activeCategory.icon]}
          <span>{activeCategory.label}</span>
        </div>

        <button
          type="button"
          onClick={handleCloseCategory}
          aria-label="Close prompt suggestions"
          className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
        >
          <X className="size-3.5" />
        </button>
      </div>

      <div className="divide-y divide-border/50 px-1.5 py-1">
        {activeCategory.items.map((item) => (
          <button
            key={item.label}
            type="button"
            onMouseEnter={() => onHoverPrompt(item.prompt)}
            onFocus={() => onHoverPrompt(item.prompt)}
            onClick={() => {
              onHoverPrompt(null);
              onSelectPrompt(item.prompt);
              setActiveCategory(null);
            }}
            className="group flex w-full items-center justify-between gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-foreground/85 hover:bg-muted/60 hover:text-foreground transition-colors cursor-pointer"
          >
            <span className="truncate">{item.label}</span>
            <ChevronRight className="size-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
};
