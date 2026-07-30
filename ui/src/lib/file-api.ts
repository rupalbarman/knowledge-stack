import type { DownloadUrlResponse, FileObject, TaskObject } from "@/common";
import { api } from "./api";

export const fileApi = {
  listByFolder(folderId: string | null) {
    return api.get<FileObject[]>(
      "/files",
      folderId ? { folder_id: folderId } : undefined,
    );
  },
  upload(file: File, folderId: string | null) {
    const formData = new FormData();
    formData.append("file", file);
    if (folderId) {
      formData.append("folder_id", folderId);
    }
    return api.upload<FileObject>("/files", formData);
  },
  getDownloadUrl(fileId: string) {
    return api.get<DownloadUrlResponse>(`/files/${fileId}/download-url`);
  },
  sync(fileId: string) {
    return api.post<TaskObject>(`/files/${fileId}/sync`);
  },
  delete(fileId: string) {
    return api.delete<void>(`/files/${fileId}`);
  },
};
