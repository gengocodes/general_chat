"use client";

import { FC } from "react";
import { ExternalLink, Globe } from "lucide-react";
import { DiscoveredSource } from "../types/chat.types";

interface AgentWebSourcesProps {
  content: string;
}

const extractMarkdownSources = (content: string): DiscoveredSource[] => {
  if (!content) return [];
  const linkRegex = /\[([^[\]]+)\]\((https?:\/\/[^\s()]+)\)/g;
  const sources: DiscoveredSource[] = [];
  const seenUrls = new Set<string>();

  let match: RegExpExecArray | null;
  while ((match = linkRegex.exec(content)) !== null) {
    const rawTitle = match[1].trim();
    const url = match[2].trim();

    if (!seenUrls.has(url)) {
      seenUrls.add(url);
      let domain = url;
      try {
        domain = new URL(url).hostname.replace(/^www\./, "");
      } catch {
        domain = url;
      }
      sources.push({
        title: rawTitle,
        url,
        domain,
      });
    }
  }
  return sources;
};

export const AgentWebSources: FC<AgentWebSourcesProps> = ({ content }) => {
  const sources = extractMarkdownSources(content);

  if (sources.length === 0) return null;

  return (
    <div className="flex items-center gap-2 flex-wrap px-1 pt-1 animate-in fade-in-50">
      <div className="flex items-center gap-1.5 text-xxxs font-semibold text-muted-foreground/70 uppercase tracking-wider shrink-0">
        <Globe className="size-3 text-primary shrink-0" />
        <span>Sources</span>
      </div>

      <div className="flex items-center gap-1.5 flex-wrap">
        {sources.map((source, idx) => (
          <a
            key={source.url}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            title={source.title}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xxs font-medium bg-muted/40 dark:bg-muted/30 border border-border/50 hover:border-primary/50 hover:bg-primary/10 hover:text-primary transition-all duration-150 cursor-pointer shadow-2xs group"
          >
            <span className="size-3.5 rounded-full bg-primary/15 text-primary flex items-center justify-center text-xxxs font-bold shrink-0">
              {idx + 1}
            </span>
            <span className="max-w-32.5 truncate text-foreground/80 group-hover:text-primary transition-colors">
              {source.domain}
            </span>
            <ExternalLink className="size-2.5 text-muted-foreground/50 group-hover:text-primary shrink-0 transition-colors" />
          </a>
        ))}
      </div>
    </div>
  );
};
