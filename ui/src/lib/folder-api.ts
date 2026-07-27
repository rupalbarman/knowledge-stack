import type { FolderObject, FolderTreeNode } from "@/common";
import { api } from "./api";

export const folderApi = {
  getTree() {
    return api.get<FolderTreeNode[]>("/folders/tree");
  },
  create(payload: { name: string; parentId: string | null }) {
    return api.post<FolderObject>("/folders", {
      name: payload.name,
      parent_id: payload.parentId,
    });
  },
};
