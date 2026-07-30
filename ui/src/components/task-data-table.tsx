import { useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type ColumnFiltersState,
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

import { DataTableFacetFilter } from "@/components/data-table-facet-filter";
import { StatusPill, type StatusPillInfo } from "@/components/status-pill";
import type { TaskObject, TaskStatus } from "@/common";
import { taskHooks } from "@/hooks/task-hooks";
import { capitalize } from "@/lib/utils";

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
    // accessorFn (capitalized text) still drives sorting/faceting - the cell
    // reads the raw value separately since TASK_STATUS_INFO is keyed by the
    // lowercase TaskStatus literals, not the capitalized display string.
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
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  });

  const { data, isLoading, isError } = taskHooks.useTasks({
    fileId,
    limit: pagination.pageSize,
    offset: pagination.pageIndex * pagination.pageSize,
  });

  const pageCount = data ? Math.ceil(data.total / pagination.pageSize) : 0;

  const table = useReactTable({
    data: data?.items ?? [],
    columns,
    state: { sorting, columnFilters, pagination },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
    // The API paginates server-side (limit/offset) - manualPagination tells
    // react-table not to slice the data itself, just track the state.
    manualPagination: true,
    pageCount,
    getCoreRowModel: getCoreRowModel(),
    // Sorting and the status filter below only see the currently loaded page
    // - /tasks has no order_by or status query param, so both are scoped to
    // "within this page" until the backend supports them server-side.
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
  });

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">Loading tasks...</p>;
  }

  if (isError) {
    return <p className="text-destructive text-sm">Failed to load tasks.</p>;
  }

  if (!data || data.items.length === 0) {
    return <p className="text-muted-foreground text-sm">No tasks</p>;
  }

  const statusColumn = table.getColumn("status");
  const rows = table.getRowModel().rows;
  const isFiltered = columnFilters.length > 0;

  return (
    <div className="space-y-3">
      {statusColumn && <DataTableFacetFilter column={statusColumn} />}

      {rows.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          No tasks match this filter
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
          {isFiltered ? (
            `${rows.length} matching on this page`
          ) : (
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
