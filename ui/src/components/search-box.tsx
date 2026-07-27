import { type SubmitEvent, useState } from "react";
import { Dialog } from "radix-ui";
import { Search } from "lucide-react";

import { searchHooks } from "@/hooks/search-hooks";

type SearchBoxProps = {
  folderId: string | null;
};

export function SearchBox({ folderId }: SearchBoxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const search = searchHooks.useSearch();

  function handleSearch(event: SubmitEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    search.mutate({ query: trimmed, folderId });
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="border-border text-muted-foreground hover:bg-accent flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm"
      >
        <Search className="size-4" />
        Search
      </button>

      <Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/40" />
          <Dialog.Content className="bg-card text-card-foreground fixed top-1/2 left-1/2 w-xl -translate-x-1/2 -translate-y-1/2 rounded-lg p-6 shadow-lg">
            <Dialog.Title className="text-base font-semibold">
              Search
            </Dialog.Title>

            <form onSubmit={handleSearch} className="mt-4 flex gap-2">
              <input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search content within this folder"
                className="border-border flex-1 rounded-md border bg-transparent px-3 py-2 text-sm"
              />
              <button
                type="submit"
                disabled={search.isPending}
                className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                {search.isPending ? "Searching..." : "Search"}
              </button>
            </form>

            {search.isError && (
              <p className="text-destructive mt-3 text-sm">
                Something went wrong, please try again
              </p>
            )}

            {search.data && (
              <div className="mt-4 max-h-96 space-y-3 overflow-y-auto">
                {search.data.hits.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No results</p>
                ) : (
                  search.data.hits.map((hit, index) => (
                    <div
                      key={`${hit.file_id}-${hit.chunk_index}-${index}`}
                      className="border-border rounded-md border p-3"
                    >
                      <p className="text-muted-foreground text-xs font-medium">
                        {hit.file_name}
                      </p>
                      <p className="mt-1 text-sm">{hit.text}</p>
                    </div>
                  ))
                )}
              </div>
            )}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
