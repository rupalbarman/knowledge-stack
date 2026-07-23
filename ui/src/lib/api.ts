import axios, {
  AxiosError,
  HttpStatusCode,
  isAxiosError,
  type AxiosRequestConfig,
  type AxiosResponse,
} from "axios";
import qs from "qs";

import { authenticationSession } from "@/lib/authentication-session";
import { ErrorCode } from "@/common";

export const API_BASE_URL =
  import.meta.env.VITE_BACKEND_URL ?? window.location.origin;
export const API_URL = `${API_BASE_URL}`;

const disallowedRoutes = [
  "/auth/login",
  "/auth/sign-up",
  "/webhooks",
];

function isUrlRelative(url: string) {
  return !url.startsWith("http") && !url.startsWith("https");
}

function globalErrorHandler(error: AxiosError) {
  if (api.isError(error)) {
    const errorCode: ErrorCode | undefined = (
      error.response?.data as { code: ErrorCode }
    )?.code;
    if (
      errorCode === ErrorCode.SESSION_EXPIRED ||
      errorCode === ErrorCode.INVALID_BEARER_TOKEN
    ) {
      authenticationSession.logOut();
      console.log(errorCode);
      window.location.href = "/sign-in";
    }
  }
}

function request<TResponse>(
  url: string,
  config: AxiosRequestConfig = {},
): Promise<TResponse> {
  const resolvedUrl = !isUrlRelative(url) ? url : `${API_URL}${url}`;
  const isApWebsite = resolvedUrl.startsWith(API_URL);
  const unAuthenticated = disallowedRoutes.some((route) =>
    resolvedUrl.replace(API_URL, "").startsWith(route),
  );

  return axios({
    url: resolvedUrl,
    ...config,
    headers: {
      Authorization: getToken(
        unAuthenticated,
        isApWebsite,
        authenticationSession.getToken(),
      ),
      ...config.headers,
    },
  })
    .then((response) =>
      config.responseType === "blob"
        ? response.data
        : (response.data as TResponse),
    )
    .catch((error) => {
      if (isAxiosError(error)) {
        globalErrorHandler(error);
      }
      throw error;
    });
}

function getToken(
  unAuthenticated: boolean,
  isApWebsite: boolean,
  token: string | null,
) {
  if (unAuthenticated || !isApWebsite) {
    return undefined;
  }
  if (!token) {
    return undefined;
  }
  return `Bearer ${token}`;
}

export type HttpError = AxiosError<unknown, AxiosResponse<unknown>>;

export const api = {
  isError(error: unknown): error is HttpError {
    return isAxiosError(error);
  },
  any: <TResponse>(url: string, config?: AxiosRequestConfig) =>
    request<TResponse>(url, config),
  get: <TResponse>(url: string, query?: unknown, config?: AxiosRequestConfig) =>
    request<TResponse>(url, {
      params: query,
      paramsSerializer: (params) => {
        return qs.stringify(params, {
          arrayFormat: "repeat",
        });
      },
      ...config,
    }),
  delete: <TResponse>(
    url: string,
    query?: Record<string, string>,
    body?: unknown,
  ) =>
    request<TResponse>(url, {
      method: "DELETE",
      params: query,
      data: body,
      paramsSerializer: (params) => {
        return qs.stringify(params, {
          arrayFormat: "repeat",
        });
      },
    }),
  post: <TResponse, TBody = unknown, TParams = unknown>(
    url: string,
    body?: TBody,
    params?: TParams,
    headers?: Record<string, string>,
  ) =>
    request<TResponse>(url, {
      method: "POST",
      data: body,
      headers: { "Content-Type": "application/json", ...headers },
      params: params,
    }),

  patch: <TResponse, TBody = unknown, TParams = unknown>(
    url: string,
    body?: TBody,
    params?: TParams,
  ) =>
    request<TResponse>(url, {
      method: "PATCH",
      data: body,
      headers: { "Content-Type": "application/json" },
      params: params,
    }),
  httpStatus: HttpStatusCode,
};
