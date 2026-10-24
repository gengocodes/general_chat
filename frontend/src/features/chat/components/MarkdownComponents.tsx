"use client";

import { AnchorHTMLAttributes, FC, HTMLAttributes } from "react";
import { ExternalLink } from "lucide-react";
import { resolveBackendUrl } from "@/shared/api/stream";
import {
  isFileDownloadUrl,
  resolveDownloadFilename,
} from "@/shared/lib/file-utils";
import { cn, flattenChildrenText } from "@/shared/lib/utils";
import { GeneratedFileCard } from "@/shared/ui/file-card";

const MarkdownLink: FC<AnchorHTMLAttributes<HTMLAnchorElement>> = ({
  href,
  children,
}) => {
  const resolvedHref = href ? resolveBackendUrl(href) : undefined;

  if (resolvedHref && isFileDownloadUrl(href)) {
    const labelText = flattenChildrenText(children);
    const filename = resolveDownloadFilename(resolvedHref, labelText);
    return <GeneratedFileCard href={resolvedHref} filename={filename} />;
  }

  return (
    <a
      href={resolvedHref}
      target="_blank"
      rel="noopener noreferrer"
      className="text-foreground font-medium underline decoration-muted-foreground/50 hover:decoration-foreground inline-flex items-center gap-1 cursor-pointer underline-offset-3 transition-colors"
    >
      {children}
      <ExternalLink className="size-3 inline shrink-0 opacity-70" />
    </a>
  );
};

export const MARKDOWN_COMPONENTS = {
  a: MarkdownLink,
  h1: ({ children }: HTMLAttributes<HTMLHeadingElement>) => (
    <h1 className="text-xl font-bold text-foreground mt-4 mb-2 tracking-tight">
      {children}
    </h1>
  ),
  h2: ({ children }: HTMLAttributes<HTMLHeadingElement>) => (
    <h2 className="text-lg font-semibold text-foreground mt-3.5 mb-1.5 tracking-tight">
      {children}
    </h2>
  ),
  h3: ({ children }: HTMLAttributes<HTMLHeadingElement>) => (
    <h3 className="text-base font-semibold text-foreground mt-3 mb-1 tracking-tight">
      {children}
    </h3>
  ),
  p: ({ children }: HTMLAttributes<HTMLParagraphElement>) => (
    <div className="leading-relaxed mb-2.5 last:mb-0 text-foreground/90">
      {children}
    </div>
  ),
  ul: ({ children }: HTMLAttributes<HTMLUListElement>) => (
    <ul className="list-disc pl-5 my-2 space-y-1 text-foreground/90">
      {children}
    </ul>
  ),
  ol: ({ children }: HTMLAttributes<HTMLOListElement>) => (
    <ol className="list-decimal pl-5 my-2 space-y-1 text-foreground/90">
      {children}
    </ol>
  ),
  li: ({ children }: HTMLAttributes<HTMLLIElement>) => (
    <li className="leading-relaxed pl-0.5">{children}</li>
  ),
  blockquote: ({ children }: HTMLAttributes<HTMLQuoteElement>) => (
    <blockquote className="border-l-2 border-foreground/30 bg-muted/40 pl-3.5 py-2 my-2.5 italic rounded-r-lg text-foreground/90">
      {children}
    </blockquote>
  ),
  pre: ({ children }: HTMLAttributes<HTMLPreElement>) => (
    <pre className="my-3 overflow-x-auto rounded-xl border border-border bg-muted/60 p-3.5 font-mono text-xs leading-relaxed text-foreground">
      {children}
    </pre>
  ),
  code: ({ className, children, ...props }: HTMLAttributes<HTMLElement>) => {
    const isBlock = Boolean(className && className.includes("language-"));
    if (isBlock) {
      return (
        <code className={cn("font-mono text-xs", className)} {...props}>
          {children}
        </code>
      );
    }
    return (
      <code
        className={cn(
          "font-mono text-xs bg-muted/80 text-foreground px-1.5 py-0.5 rounded border border-border/60 font-medium",
          className,
        )}
        {...props}
      >
        {children}
      </code>
    );
  },
  del: ({ children }: HTMLAttributes<HTMLElement>) => (
    <del className="line-through text-muted-foreground">{children}</del>
  ),
  hr: () => <hr className="my-3.5 border-border/70" />,
  table: ({ children }: HTMLAttributes<HTMLTableElement>) => (
    <div className="my-3 w-full overflow-x-auto rounded-xl border border-border bg-card shadow-2xs">
      <table className="w-full text-left text-xs border-collapse">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }: HTMLAttributes<HTMLTableSectionElement>) => (
    <thead className="bg-muted/60 border-b border-border text-foreground font-semibold uppercase tracking-wider text-[11px]">
      {children}
    </thead>
  ),
  tbody: ({ children }: HTMLAttributes<HTMLTableSectionElement>) => (
    <tbody className="divide-y divide-border/50 bg-card text-foreground">
      {children}
    </tbody>
  ),
  tr: ({ children }: HTMLAttributes<HTMLTableRowElement>) => (
    <tr className="transition-colors hover:bg-muted/40">{children}</tr>
  ),
  th: ({ children }: HTMLAttributes<HTMLTableCellElement>) => (
    <th className="px-3.5 py-2.5 font-semibold text-foreground/90 whitespace-nowrap">
      {children}
    </th>
  ),
  td: ({ children }: HTMLAttributes<HTMLTableCellElement>) => (
    <td className="px-3.5 py-2.5 text-foreground/90 align-middle">
      {children}
    </td>
  ),
};
