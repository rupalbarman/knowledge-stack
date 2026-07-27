import type {
  SignInRequest,
  AuthenticationResponse,
  SignUpRequest,
  SwitchProjectRequest,
} from "@/common";
import { api } from "@/lib/api";

export const authenticationApi = {
  signIn(request: SignInRequest) {
    return api.post<AuthenticationResponse>("/auth/sign-in", request);
  },
  signUp(request: SignUpRequest) {
    return api.post<AuthenticationResponse>("/auth/sign-up", request);
  },
  switchProject(request: SwitchProjectRequest) {
    return api.post<AuthenticationResponse>(`/auth/switch-project`, request);
  },
};
