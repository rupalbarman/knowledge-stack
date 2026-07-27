import type { SearchResponse } from "@/common";
import { api } from "./api";

export const searchApi = {
  search(payload: { query: string; folderId: string | null }) {
    return api.post<SearchResponse>("/search", {
      query: payload.query,
      folder_id: payload.folderId,
    });
  },
};
