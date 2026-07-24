import type { TaskPageResponse } from "@/common";
import { api } from "./api";

export const taskApi = {
  list(params: { fileId?: string; limit: number; offset: number }) {
    return api.get<TaskPageResponse>("/tasks", {
      file_id: params.fileId,
      limit: params.limit,
      offset: params.offset,
    });
  },
};
