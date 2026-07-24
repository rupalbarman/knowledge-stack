import type { FolderTreeNode } from "@/common";
import { api } from "./api";

export const folderApi = {
  getTree() {
    return api.get<FolderTreeNode[]>("/folders/tree");
  },
};
