import type { TaskPageResponse, TaskStatus } from "@/common";
import { api } from "./api";

export const taskApi = {
  list(params: {
    fileId?: string;
    status?: TaskStatus;
    limit: number;
    offset: number;
  }) {
    return api.get<TaskPageResponse>("/tasks", {
      file_id: params.fileId,
      status: params.status,
      limit: params.limit,
      offset: params.offset,
    });
  },
};
