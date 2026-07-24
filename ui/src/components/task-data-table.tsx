import { useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type PaginationState,
  type SortingState,
} from '@tanstack/react-table'
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

import type { TaskObject } from '@/common'
import { taskHooks } from '@/hooks/task-hooks'

const columns: ColumnDef<TaskObject>[] = [
  { accessorKey: 'file_name', header: 'File' },
  { accessorKey: 'type', header: 'Type' },
  { accessorKey: 'reason', header: 'Reason' },
  { accessorKey: 'status', header: 'Status' },
  {
    accessorKey: 'error',
    header: 'Error',
    cell: ({ getValue }) => getValue<string | null>() ?? '-',
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

type TaskDataTableProps = {
  fileId?: string
}

export function TaskDataTable({ fileId }: TaskDataTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  })

  const { data, isLoading, isError } = taskHooks.useTasks({
    fileId,
    limit: pagination.pageSize,
    offset: pagination.pageIndex * pagination.pageSize,
  })

  const pageCount = data ? Math.ceil(data.total / pagination.pageSize) : 0

  const table = useReactTable({
    data: data?.items ?? [],
    columns,
    state: { sorting, pagination },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    manualPagination: true,
    pageCount,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">Loading tasks...</p>
  }

  if (isError) {
    return <p className="text-destructive text-sm">Failed to load tasks.</p>
  }

  if (!data || data.items.length === 0) {
    return <p className="text-muted-foreground text-sm">No tasks</p>
  }

  return (
    <div className="space-y-3">
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

      <div className="flex items-center justify-end gap-3 text-sm">
        <span className="text-muted-foreground">
          {pagination.pageIndex * pagination.pageSize + 1}-
          {Math.min(
            pagination.pageIndex * pagination.pageSize + data.items.length,
            data.total,
          )}{' '}
          of {data.total}
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
  )
}
