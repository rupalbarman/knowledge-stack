import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ANALYTICS_SUMMARY_KEY } from "@/hooks/analytics-hooks";
import { folderApi } from "@/lib/folder-api";

export const folderHooks = {
  useFolderTree: () => {
    return useQuery({
      queryKey: ["folder-tree"],
      queryFn: () => folderApi.getTree(),
    });
  },
  useCreateFolder: () => {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: (payload: { name: string; parentId: string | null }) =>
        folderApi.create(payload),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["folder-tree"] });
        queryClient.invalidateQueries({ queryKey: ANALYTICS_SUMMARY_KEY });
      },
    });
  },
};
