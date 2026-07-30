import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export type StatusPillInfo = {
  label: string;
  className: string;
  explanation: string;
};

// Shared rendering for any {label, className, explanation} status - callers
// own their own Record<TaskStatus, StatusPillInfo> map, since the same
// TaskStatus values read differently in different contexts (e.g. a
// completed delete_vectors task isn't "indexed").
export function StatusPill({ info }: { info: StatusPillInfo }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
            info.className,
          )}
        >
          {info.label}
        </span>
      </TooltipTrigger>
      <TooltipContent>{info.explanation}</TooltipContent>
    </Tooltip>
  );
}
