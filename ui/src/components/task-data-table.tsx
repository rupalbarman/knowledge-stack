import { useEffect, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type PaginationState,
  type SortingState,
} from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import { StatusPill, type StatusPillInfo } from "@/components/status-pill";
import type { TaskObject, TaskStatus } from "@/common";
import { taskHooks } from "@/hooks/task-hooks";
import { capitalize, cn } from "@/lib/utils";

// Record<TaskStatus, ...> so TS errors if file-api TaskStatus ever
// gains/loses a value and this falls out of sync.
const TASK_STATUS_INFO: Record<TaskStatus, StatusPillInfo> = {
  pending: {
    label: "Pending",
    className: "bg-muted text-muted-foreground",
    explanation: "Queued, waiting to be picked up for processing.",
  },
  processing: {
    label: "Processing",
    className: "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400",
    explanation: "Currently running.",
  },
  completed: {
    label: "Completed",
    className:
      "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400",
    explanation: "Finished successfully.",
  },
  failed: {
    label: "Failed",
    className: "bg-destructive/10 text-destructive",
    explanation: "Something went wrong while running this task.",
  },
  superseded: {
    label: "Superseded",
    className: "bg-muted text-muted-foreground",
    explanation:
      "A newer task for the same file replaced this one before it finished.",
  },
};

const columns: ColumnDef<TaskObject>[] = [
  { accessorKey: "file_name", header: "File" },
  { accessorKey: "type", header: "Type" },
  {
    accessorKey: "reason",
    header: "Reason",
    accessorFn: (row) => capitalize(row.reason),
  },
  {
    accessorKey: "status",
    header: "Status",
    // accessorFn (capitalized text) drives sorting (still client-side,
    // current-page-only) - the cell reads the raw value separately since
    // TASK_STATUS_INFO is keyed by the lowercase TaskStatus literals, not the
    // capitalized display string. Filtering by status is server-side (see
    // the facet buttons below), not driven by this column at all.
    accessorFn: (row) => capitalize(row.status),
    cell: ({ row }) => (
      <StatusPill info={TASK_STATUS_INFO[row.original.status]} />
    ),
  },
  {
    accessorKey: "error",
    header: "Error",
    cell: ({ getValue }) => getValue<string | null>() ?? "-",
  },
  {
    accessorKey: "created_at",
    header: "Created",
    cell: ({ getValue }) => new Date(getValue<string>()).toLocaleString(),
  },
];

function SortIcon({ direction }: { direction: false | "asc" | "desc" }) {
  if (direction === "asc") return <ArrowUp className="size-3.5" />;
  if (direction === "desc") return <ArrowDown className="size-3.5" />;
  return <ArrowUpDown className="size-3.5 opacity-40" />;
}

type TaskDataTableProps = {
  fileId?: string;
};

export function TaskDataTable({ fileId }: TaskDataTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [selectedStatus, setSelectedStatus] = useState<TaskStatus>();
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 50,
  });

  // Reset to the first page whenever the status filter changes - otherwise
  // picking a filter while on, say, page 3 could request an offset that
  // doesn't exist within the filtered result set.
  useEffect(() => {
    setPagination((p) => ({ ...p, pageIndex: 0 }));
  }, [selectedStatus]);

  const { data, isLoading, isError } = taskHooks.useTasks({
    fileId,
    status: selectedStatus,
    limit: pagination.pageSize,
    offset: pagination.pageIndex * pagination.pageSize,
  });

  const pageCount = data ? Math.ceil(data.total / pagination.pageSize) : 0;

  const table = useReactTable({
    data: data?.items ?? [],
    columns,
    state: { sorting, pagination },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    // The API paginates and filters by status server-side - manualPagination
    // tells react-table not to slice the data itself, just track the state,
    // and manualFiltering confirms there's no client-side filterFn to run.
    manualPagination: true,
    manualFiltering: true,
    pageCount,
    getCoreRowModel: getCoreRowModel(),
    // Sorting still only sees the currently loaded page - /tasks has no
    // order_by query param yet.
    getSortedRowModel: getSortedRowModel(),
  });

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">Loading tasks...</p>;
  }

  if (isError) {
    return <p className="text-destructive text-sm">Failed to load tasks.</p>;
  }

  const rows = table.getRowModel().rows;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {(Object.entries(TASK_STATUS_INFO) as [TaskStatus, StatusPillInfo][]).map(
          ([value, info]) => (
            <button
              key={value}
              type="button"
              onClick={() =>
                setSelectedStatus(selectedStatus === value ? undefined : value)
              }
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium",
                selectedStatus === value
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border text-foreground hover:bg-accent",
              )}
            >
              {info.label}
            </button>
          ),
        )}
      </div>

      {!data || data.items.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          {selectedStatus ? "No tasks match this filter" : "No tasks"}
        </p>
      ) : (
        <table className="w-full text-left">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr
                key={headerGroup.id}
                className="border-border border-b text-sm font-medium"
              >
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="px-3 py-2">
                    <button
                      type="button"
                      onClick={header.column.getToggleSortingHandler()}
                      className="flex items-center gap-1"
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                      <SortIcon direction={header.column.getIsSorted()} />
                    </button>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-border border-b">
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="text-muted-foreground px-3 py-2 text-sm"
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="flex items-center justify-end gap-3 text-sm">
        <span className="text-muted-foreground">
          {data && data.items.length > 0 && (
            <>
              {pagination.pageIndex * pagination.pageSize + 1}-
              {Math.min(
                pagination.pageIndex * pagination.pageSize + data.items.length,
                data.total,
              )}{" "}
              of {data.total}
            </>
          )}
        </span>
        <button
          type="button"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
          className="hover:bg-accent rounded-md p-1.5 disabled:opacity-40"
          aria-label="Previous page"
        >
          <ChevronLeft className="size-4" />
        </button>
        <button
          type="button"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
          className="hover:bg-accent rounded-md p-1.5 disabled:opacity-40"
          aria-label="Next page"
        >
          <ChevronRight className="size-4" />
        </button>
      </div>
    </div>
  );
}
