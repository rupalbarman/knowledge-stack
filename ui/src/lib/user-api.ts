import type { UserWithMetaInformationAndProject } from "@/common";
import { api } from "./api";

export const userApi = {
  getCurrentUser() {
    return api.get<UserWithMetaInformationAndProject>("/users/me");
  },
};
