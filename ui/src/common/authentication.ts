export type SignInResponse = {
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

export type SignUpResponse = {
  id: string;
  email: string;
};

export type SwitchProjectRequest = {
  projectId: string;
};
