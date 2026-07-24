import type { FileObject } from "@/common";
import { api } from "./api";

export const fileApi = {
  listByFolder(folderId: string | null) {
    return api.get<FileObject[]>(
      "/files",
      folderId ? { folder_id: folderId } : undefined,
    );
  },
};
