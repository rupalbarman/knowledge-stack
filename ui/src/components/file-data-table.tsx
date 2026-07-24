import { useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'

import type { FileObject } from '@/common'
import { fileHooks } from '@/hooks/file-hooks'

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let value = bytes / 1024
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`
}

// Only sorting is wired up for now - getFilteredRowModel/columnFilters can
// slot in the same way once there's a design for per-column filter inputs.
const columns: ColumnDef<FileObject>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'content_type',
    header: 'Content type',
    cell: ({ getValue }) => getValue<string | null>() ?? '-',
  },
  {
    accessorKey: 'size_bytes',
    header: 'Size',
    cell: ({ getValue }) => formatBytes(getValue<number>()),
  },
  {
    accessorKey: 'created_at',
    header: 'Created',
    cell: ({ getValue }) => new Date(getValue<string>()).toLocaleString(),
  },
]

function SortIcon({ direction }: { direction: false | 'asc' | 'desc' }) {
  if (direction === 'asc') return <ArrowUp className="size-3.5" />
  if (direction === 'desc') return <ArrowDown className="size-3.5" />
  return <ArrowUpDown className="size-3.5 opacity-40" />
}

type FileDataTableProps = {
  folderId: string | null
}

export function FileDataTable({ folderId }: FileDataTableProps) {
  const { data, isLoading, isError } = fileHooks.useFilesByFolder(folderId)
  const [sorting, setSorting] = useState<SortingState>([])

  const table = useReactTable({
    data: data ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">Loading files...</p>
  }

  if (isError) {
    return <p className="text-destructive text-sm">Failed to load files.</p>
  }

  if (!data || data.length === 0) {
    return <p className="text-muted-foreground text-sm">No files</p>
  }

  return (
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
        {table.getRowModel().rows.map((row) => (
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
  )
}
