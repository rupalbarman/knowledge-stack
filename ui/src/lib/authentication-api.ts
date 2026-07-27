import type {
  SignInRequest,
  SignInResponse,
  SignUpRequest,
  SignUpResponse,
  SwitchProjectRequest,
} from "@/common";
import { api } from "@/lib/api";

export const authenticationApi = {
  signIn(request: SignInRequest) {
    return api.post<SignInResponse>("/auth/sign-in", request);
  },
  signUp(request: SignUpRequest) {
    return api.post<SignUpResponse>("/auth/sign-up", request);
  },
  switchProject(request: SwitchProjectRequest) {
    return api.post<SignInResponse>(`/auth/switch-project`, request);
  },
};
