import type { FileObject } from "@/common";
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
};
