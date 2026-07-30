import { useEffect, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  type VisibilityState,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

import { DataTableFacetFilter } from "@/components/data-table-facet-filter";
import type { FileObject } from "@/common";
import { fileHooks } from "@/hooks/file-hooks";
import { cn } from "@/lib/utils";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

// Show file icons as badges denoting their extension instead of MIME type
// Fallback to using MIME type if no extension is present
// Fallback to using FILE when MIME fails too.
function getFileTypeLabel(name: string, contentType: string | null) {
  const lastDot = name.lastIndexOf(".");
  if (lastDot !== -1 && lastDot !== name.length - 1) {
    return name.slice(lastDot + 1).toUpperCase();
  }
  const subtype = contentType?.split("/")[1];
  return subtype ? subtype.toUpperCase() : "FILE";
}

function FileTypeBadge({ label }: { label: string }) {
  const display = label.length > 4 ? label.slice(0, 4) : label;
  return (
    <span
      title={label}
      className="bg-muted text-muted-foreground inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[10px] font-semibold tracking-wide"
    >
      {display}
    </span>
  );
}

const columns: ColumnDef<FileObject>[] = [
  {
    // Filter/facet-only column, hidden via columnVisibility below - drives
    // the extension pill row
    id: "extension",
    accessorFn: (row) => getFileTypeLabel(row.name, row.content_type),
    header: "Type",
  },
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <FileTypeBadge label={row.getValue<string>("extension")} />
        <span>{row.original.name}</span>
      </div>
    ),
  },
  {
    accessorKey: "size_bytes",
    header: "Size",
    cell: ({ getValue }) => formatBytes(getValue<number>()),
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

type FileDataTableProps = {
  folderId: string | null;
  highlightedFileId?: string | null;
};

export function FileDataTable({
  folderId,
  highlightedFileId,
}: FileDataTableProps) {
  const { data, isLoading, isError } = fileHooks.useFilesByFolder(folderId);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility] = useState<VisibilityState>({ extension: false });

  useEffect(() => {
    if (!highlightedFileId) return;
    document
      .querySelector(`[data-file-id="${highlightedFileId}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlightedFileId]);

  const table = useReactTable({
    data: data ?? [],
    columns,
    state: { sorting, columnFilters, columnVisibility },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
  });

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">Loading files...</p>;
  }

  if (isError) {
    return <p className="text-destructive text-sm">Failed to load files.</p>;
  }

  if (!data || data.length === 0) {
    return <p className="text-muted-foreground text-sm">No files</p>;
  }

  const extensionColumn = table.getColumn("extension");
  const rows = table.getRowModel().rows;

  return (
    <div className="space-y-3">
      {extensionColumn && <DataTableFacetFilter column={extensionColumn} />}

      {rows.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          No files match this filter
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
              <tr
                key={row.id}
                data-file-id={row.original.id}
                className={cn(
                  "border-border border-b transition-colors duration-1000",
                  row.original.id === highlightedFileId && "bg-primary/10",
                )}
              >
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
    </div>
  );
}
