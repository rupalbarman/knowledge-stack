// Matches file-api's TokenResponse (POST /auth/login) - no user/project info is
// returned at login, only the token. Fetch that separately via GET /users/me.
export type AuthenticationResponse = {
  access_token: string;
  token_type: string;
};

export type SignInRequest = {
  email: string;
  password: string;
};

export type SignOutRequest = {
  token: string;
};

export type SignUpRequest = {
  email: string;
  password: string;
};

export type SwitchProjectRequest = {
  projectId: string;
};
