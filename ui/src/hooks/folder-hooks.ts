import { useQuery } from "@tanstack/react-query";

import { folderApi } from "@/lib/folder-api";

export const folderHooks = {
  useFolderTree: () => {
    return useQuery({
      queryKey: ["folder-tree"],
      queryFn: () => folderApi.getTree(),
    });
  },
};
