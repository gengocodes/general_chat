"use client";

import { useState, FC } from "react";
import { Brain, CheckCircle2, ChevronRight } from "lucide-react";
import { AgentActivity } from "../types/chat.types";
import { Marker, MarkerIcon, MarkerContent } from "@/shared/ui/marker";
import { Spinner } from "@/shared/ui/spinner";
import { cn } from "@/shared/lib/utils";

interface AgentExecutionTimelineProps {
  activities?: AgentActivity[];
  executionTimeSeconds?: number;
}

const renderActivityIcon = (activity: AgentActivity) => {
  if (activity.status === "completed") {
    return <CheckCircle2 className="size-3.5 text-primary shrink-0" />;
  }

  return <Spinner className="size-3.5 text-primary shrink-0" />;
};

export const AgentExecutionTimeline: FC<AgentExecutionTimelineProps> = ({
  activities,
  executionTimeSeconds,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  const hasActivities = activities && activities.length > 0;
  const hasContent = hasActivities || executionTimeSeconds !== undefined;

  if (!hasContent) return null;

  const isComplete = executionTimeSeconds !== undefined;

  if (!isComplete) {
    return (
      <div className="w-full flex flex-col gap-1.5 my-1 animate-in fade-in-50">
        {hasActivities && (
          <div className="flex flex-col gap-1.5 pl-1">
            {activities.map((activity) => (
              <Marker key={activity.id} className="text-xs gap-2">
                <MarkerIcon>{renderActivityIcon(activity)}</MarkerIcon>
                <MarkerContent className="text-xs font-medium text-muted-foreground/90">
                  {activity.message}
                </MarkerContent>
              </Marker>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-1.5 my-0.5 animate-in fade-in-50">
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        className="group inline-flex items-center gap-1.5 py-0.5 text-xs font-medium text-muted-foreground/80 hover:text-foreground transition-colors cursor-pointer select-none self-start"
      >
        <Brain className="size-3.5 text-muted-foreground/70 group-hover:text-primary transition-colors shrink-0" />
        <span className="tracking-tight font-medium">
          Thought for {executionTimeSeconds} seconds
        </span>

        <ChevronRight
          className={cn(
            "size-3.5 text-muted-foreground/60 transition-transform duration-200",
            isExpanded && "rotate-90",
          )}
        />
      </button>

      {isExpanded && hasActivities && (
        <div className="flex flex-col gap-1.5 pl-3 ml-2 border-l border-primary/20 py-1.5 text-xs animate-in fade-in-50 duration-200">
          {activities.map((activity) => (
            <Marker key={activity.id} className="text-xs gap-2">
              <MarkerIcon>{renderActivityIcon(activity)}</MarkerIcon>
              <MarkerContent className="text-xs font-medium text-muted-foreground">
                {activity.message}
              </MarkerContent>
            </Marker>
          ))}
        </div>
      )}
    </div>
  );
};
