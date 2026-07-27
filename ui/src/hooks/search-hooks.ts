import { useMutation } from "@tanstack/react-query";

import { searchApi } from "@/lib/search-api";

export const searchHooks = {
  // Mutation, not query - search fires on an explicit button click, not
  // automatically on mount/dependency change.
  useSearch: () => {
    return useMutation({
      mutationFn: (payload: { query: string; folderId: string | null }) =>
        searchApi.search(payload),
    });
  },
};
