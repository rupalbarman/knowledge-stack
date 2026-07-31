import { Files, Folder, HardDrive, Layers } from "lucide-react";

import type { DocumentStatusBreakdown } from "@/common";
import { analyticsHooks } from "@/hooks/analytics-hooks";
import { cn, formatBytes } from "@/lib/utils";

const STATUS_ORDER: (keyof DocumentStatusBreakdown)[] = [
  "completed",
  "processing",
  "pending",
  "failed",
];

const STATUS_LABELS: Record<
  keyof DocumentStatusBreakdown,
  { label: string; dotClassName: string }
> = {
  completed: { label: "Indexed", dotClassName: "bg-green-500" },
  processing: { label: "Processing", dotClassName: "bg-blue-500" },
  pending: { label: "Pending", dotClassName: "bg-muted-foreground" },
  failed: { label: "Failed", dotClassName: "bg-destructive" },
};

type AnalyticsCardProps = {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  children?: React.ReactNode;
};

function AnalyticsCard({ icon: Icon, label, value, children }: AnalyticsCardProps) {
  return (
    <div className="bg-card text-card-foreground border-border flex flex-1 flex-col gap-3 rounded-md border p-4">
      <div className="flex items-center gap-2">
        <span className="bg-primary/10 text-primary inline-flex size-8 items-center justify-center rounded-md">
          <Icon className="size-4" />
        </span>
        <span className="text-muted-foreground text-sm">{label}</span>
      </div>
      <span className="text-2xl font-semibold">{value}</span>
      {children}
    </div>
  );
}

export function AnalyticsBar() {
  const { data } = analyticsHooks.useSummary();

  const placeholder = "—";

  return (
    <div className="flex flex-wrap gap-4">
      <AnalyticsCard
        icon={Files}
        label="Total Documents"
        value={data ? String(data.total_documents) : placeholder}
      >
        {data && (
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {STATUS_ORDER.filter((status) => data.documents_by_status[status] > 0).map(
              (status) => (
                <span
                  key={status}
                  className="text-muted-foreground inline-flex items-center gap-1.5 text-xs"
                >
                  <span
                    className={cn(
                      "size-1.5 rounded-full",
                      STATUS_LABELS[status].dotClassName,
                    )}
                  />
                  {data.documents_by_status[status]} {STATUS_LABELS[status].label}
                </span>
              ),
            )}
          </div>
        )}
      </AnalyticsCard>

      <AnalyticsCard
        icon={Folder}
        label="Total Folders"
        value={data ? String(data.total_folders) : placeholder}
      />

      <AnalyticsCard
        icon={HardDrive}
        label="Storage Used"
        value={data ? formatBytes(data.storage_used_bytes) : placeholder}
      />

      <AnalyticsCard
        icon={Layers}
        label="Chunks Indexed"
        value={data ? String(data.total_chunks) : placeholder}
      />
    </div>
  );
}
