import { useQuery } from "@tanstack/react-query";

import { fileApi } from "@/lib/file-api";

export const fileHooks = {
  useFilesByFolder: (folderId: string | null) => {
    return useQuery({
      queryKey: ["files", folderId],
      queryFn: () => fileApi.listByFolder(folderId),
    });
  },
};
