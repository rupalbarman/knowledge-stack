import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fileApi } from "@/lib/file-api";

export const fileHooks = {
  useFilesByFolder: (folderId: string | null) => {
    return useQuery({
      queryKey: ["files", folderId],
      queryFn: () => fileApi.listByFolder(folderId),
    });
  },
  useUploadFile: () => {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({
        file,
        folderId,
      }: {
        file: File;
        folderId: string | null;
      }) => fileApi.upload(file, folderId),
      onSuccess: (_data, variables) => {
        queryClient.invalidateQueries({
          queryKey: ["files", variables.folderId],
        });
      },
    });
  },
};
