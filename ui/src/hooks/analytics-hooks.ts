import { useQuery } from "@tanstack/react-query";

import { analyticsApi } from "@/lib/analytics-api";

export const ANALYTICS_SUMMARY_KEY = ["analytics", "summary"];

export const analyticsHooks = {
  useSummary: () => {
    return useQuery({
      queryKey: ANALYTICS_SUMMARY_KEY,
      queryFn: () => analyticsApi.getSummary(),
    });
  },
};
