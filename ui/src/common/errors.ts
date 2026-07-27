export const ErrorCode = {
  AUTHENTICATION: "AUTHENTICATION",
  AUTHORIZATION: "AUTHORIZATION",
  SESSION_EXPIRED: "SESSION_EXPIRED",
  INVALID_BEARER_TOKEN: "INVALID_BEARER_TOKEN",
} as const;

export type ErrorCode = (typeof ErrorCode)[keyof typeof ErrorCode];
