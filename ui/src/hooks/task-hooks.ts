import { useQuery } from "@tanstack/react-query";

import type { TaskStatus } from "@/common";
import { taskApi } from "@/lib/task-api";

export const taskHooks = {
  useTasks: (params: {
    fileId?: string;
    status?: TaskStatus;
    limit: number;
    offset: number;
  }) => {
    return useQuery({
      queryKey: [
        "tasks",
        params.fileId,
        params.status,
        params.limit,
        params.offset,
      ],
      queryFn: () => taskApi.list(params),
    });
  },
};
