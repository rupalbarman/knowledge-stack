import { useQuery } from "@tanstack/react-query";

import { taskApi } from "@/lib/task-api";

export const taskHooks = {
  useTasks: (params: { fileId?: string; limit: number; offset: number }) => {
    return useQuery({
      queryKey: ["tasks", params.fileId, params.limit, params.offset],
      queryFn: () => taskApi.list(params),
    });
  },
};
