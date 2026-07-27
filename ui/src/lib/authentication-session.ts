import dayjs from "dayjs";
import { jwtDecode } from "jwt-decode";

import { BrowserStorage } from "./browser-storage";
import type { AuthenticationResponse, UserPrincipal } from "@/common";
import { authenticationApi } from "./authentication-api";

const tokenKey = "token";

export const authenticationSession = {
  saveToken(token: string) {
    BrowserStorage.getInstance().setItem(tokenKey, token);
  },
  saveResponse(response: AuthenticationResponse) {
    BrowserStorage.getInstance().setItem(tokenKey, response.access_token);
    window.dispatchEvent(new Event("storage"));
  },
  isJwtExpired(token: string): boolean {
    if (!token) {
      return true;
    }
    try {
      const decoded = jwtDecode(token);
      if (decoded && decoded.exp && dayjs().isAfter(dayjs.unix(decoded.exp))) {
        return true;
      }
      return false;
    } catch (e) {
      return true;
    }
  },
  getToken(): string | null {
    return BrowserStorage.getInstance().getItem(tokenKey) ?? null;
  },
  getCurrentUserId(): string | null {
    const token = this.getToken();
    if (!token) {
      return null;
    }
    const decodedJwt = getDecodedJwt(token);
    return decodedJwt.sub;
  },
  // file-api has exactly one project per user, and the JWT carries no
  // project id (see UserPrincipal) - project switching isn't a backend
  // capability yet. Deferred along with multi-project support.
  appendProjectRoutePrefix(path: string): string {
    return path;
  },
  getProjectId(): string | null {
    return null;
  },
  async switchToProject(projectId: string) {
    if (authenticationSession.getProjectId() === projectId) {
      return;
    }
    const result = await authenticationApi.switchProject({ projectId });
    BrowserStorage.getInstance().setItem(tokenKey, result.access_token);
    window.dispatchEvent(new Event("storage"));
  },
  isLoggedIn(): boolean {
    const token = this.getToken();
    if (!token) {
      return false;
    }
    return !this.isJwtExpired(token);
  },
  clearSession() {
    BrowserStorage.getInstance().removeItem(tokenKey);
  },
  logOut() {
    this.clearSession();
    window.location.href = "/sign-in";
  },
};

function getDecodedJwt(token: string): UserPrincipal {
  return jwtDecode<UserPrincipal>(token);
}
