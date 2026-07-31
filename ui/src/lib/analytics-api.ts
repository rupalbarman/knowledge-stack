import type { AnalyticsSummary } from "@/common";
import { api } from "./api";

export const analyticsApi = {
  getSummary() {
    return api.get<AnalyticsSummary>("/analytics/summary");
  },
};
