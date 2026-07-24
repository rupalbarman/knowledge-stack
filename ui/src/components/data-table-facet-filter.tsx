import type { Column } from '@tanstack/react-table'

import { cn } from '@/lib/utils'

// Renders the distinct values present in the currently loaded rows
// (column.getFacetedUniqueValues()) as clickable pills - click one to filter
// to that value, click it again to clear. Requires getFacetedUniqueValues()
// and getFilteredRowModel() to be enabled on the table.
export function DataTableFacetFilter<TData>({
  column,
}: {
  column: Column<TData, unknown>
}) {
  const facets = column.getFacetedUniqueValues()
  const selected = column.getFilterValue() as string | undefined

  if (facets.size === 0) {
    return null
  }

  return (
    <div className="flex flex-wrap gap-2">
      {Array.from(facets.entries()).map(([value, count]) => (
        <button
          key={value}
          type="button"
          onClick={() =>
            column.setFilterValue(selected === value ? undefined : value)
          }
          className={cn(
            'rounded-full border px-3 py-1 text-xs font-medium',
            selected === value
              ? 'bg-primary text-primary-foreground border-primary'
              : 'border-border text-foreground hover:bg-accent',
          )}
        >
          {String(value)} <span className="opacity-60">{count}</span>
        </button>
      ))}
    </div>
  )
}
