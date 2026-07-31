import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ANALYTICS_SUMMARY_KEY } from "@/hooks/analytics-hooks";
import { fileApi } from "@/lib/file-api";

// Invalidates every file listing (folder-scoped and recent alike - both
// query keys start with "files") rather than a single folderId, since a
// mutated file may be visible in more than one of these views at once.
function invalidateFileLists(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ["files"] });
  queryClient.invalidateQueries({ queryKey: ANALYTICS_SUMMARY_KEY });
}

export const fileHooks = {
  useFilesByFolder: (folderId: string | null) => {
    return useQuery({
      queryKey: ["files", folderId],
      queryFn: () => fileApi.listByFolder(folderId),
    });
  },
  useRecentFiles: (limit: number, offset = 0) => {
    return useQuery({
      queryKey: ["files", "recent", limit, offset],
      queryFn: () => fileApi.listRecent(limit, offset),
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
      onSuccess: () => invalidateFileLists(queryClient),
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
      mutationFn: (fileId: string) => fileApi.sync(fileId),
      onSuccess: () => invalidateFileLists(queryClient),
    });
  },
  useDeleteFile: () => {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: (fileId: string) => fileApi.delete(fileId),
      onSuccess: () => invalidateFileLists(queryClient),
    });
  },
  useReplaceFileContent: () => {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ fileId, file }: { fileId: string; file: File }) =>
        fileApi.replaceContent(fileId, file),
      onSuccess: () => invalidateFileLists(queryClient),
    });
  },
};
