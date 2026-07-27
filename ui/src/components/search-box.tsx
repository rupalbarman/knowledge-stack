import { Search } from 'lucide-react'

// UI only for now - no search behavior wired up yet.
export function SearchBox() {
  return (
    <button
      type="button"
      className="border-border text-muted-foreground hover:bg-accent flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm"
    >
      <Search className="size-4" />
      Search
    </button>
  )
}
