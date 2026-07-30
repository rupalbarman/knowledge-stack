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
  // Mutation, not query - fetched fresh on each click rather than cached,
  // since the URL is only valid for a limited time anyway.
  useGetDownloadUrl: () => {
    return useMutation({
      mutationFn: (fileId: string) => fileApi.getDownloadUrl(fileId),
    });
  },
  useSyncFile: () => {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ fileId }: { fileId: string; folderId: string | null }) =>
        fileApi.sync(fileId),
      onSuccess: (_data, variables) => {
        queryClient.invalidateQueries({
          queryKey: ["files", variables.folderId],
        });
      },
    });
  },
  useDeleteFile: () => {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ fileId }: { fileId: string; folderId: string | null }) =>
        fileApi.delete(fileId),
      onSuccess: (_data, variables) => {
        queryClient.invalidateQueries({
          queryKey: ["files", variables.folderId],
        });
      },
    });
  },
  useReplaceFileContent: () => {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({
        fileId,
        file,
      }: {
        fileId: string;
        file: File;
        folderId: string | null;
      }) => fileApi.replaceContent(fileId, file),
      onSuccess: (_data, variables) => {
        queryClient.invalidateQueries({
          queryKey: ["files", variables.folderId],
        });
      },
    });
  },
};
