import { tokenStore } from "../auth/tokenStore";
import type { TokenPair } from "./types";
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}
export class ApiClientError extends Error implements ApiError {
  code: string;
  details?: Record<string, unknown>;
  status: number;
  constructor(error: ApiError, status: number) {
    super(error.message);
    this.name = "ApiClientError";
    this.code = error.code;
    this.details = error.details;
    this.status = status;
  }
}
const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"
).replace(/\/$/, "");
let refreshPromise: Promise<string | null> | null = null;
async function parseError(response: Response) {
  try {
    const body = (await response.json()) as { error?: ApiError };
    if (body.error) return new ApiClientError(body.error, response.status);
  } catch {
    /* безопасное сообщение ниже */
  }
  return new ApiClientError(
    { code: "http_error", message: `Ошибка HTTP ${response.status}` },
    response.status,
  );
}
async function requestNewAccessToken(refresh: string) {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
  } catch {
    // Временная ошибка сети не должна уничтожать сохранённую сессию.
    return null;
  }

  if (!response.ok) {
    const latestRefreshToken = tokenStore.getRefreshToken();
    if (latestRefreshToken && latestRefreshToken !== refresh) {
      return tokenStore.getAccessToken();
    }
    if (response.status === 401 || response.status === 403) {
      tokenStore.clear();
    }
    return null;
  }

  try {
    const pair = (await response.json()) as TokenPair;
    tokenStore.setTokens(pair.access_token, pair.refresh_token);
    return pair.access_token;
  } catch {
    return null;
  }
}

export async function refreshAccessToken() {
  const refresh = tokenStore.getRefreshToken();
  if (!refresh) return null;

  if (!refreshPromise) {
    refreshPromise = requestNewAccessToken(refresh).finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}
interface Options extends RequestInit {
  skipAuth?: boolean;
  skipRefresh?: boolean;
}
export async function apiRequest<T>(
  path: string,
  options: Options = {},
): Promise<T> {
  const { skipAuth = false, skipRefresh = false, ...request } = options;
  const headers = new Headers(request.headers);
  if (
    request.body &&
    !(request.body instanceof FormData) &&
    !headers.has("Content-Type")
  )
    headers.set("Content-Type", "application/json");
  const access = tokenStore.getAccessToken();
  if (!skipAuth && access) headers.set("Authorization", `Bearer ${access}`);
  let response = await fetch(`${apiBaseUrl}${path}`, { ...request, headers });
  if (response.status === 401 && !skipAuth && !skipRefresh) {
    const next = await refreshAccessToken();
    if (next) {
      headers.set("Authorization", `Bearer ${next}`);
      response = await fetch(`${apiBaseUrl}${path}`, { ...request, headers });
    }
  }
  if (!response.ok) throw await parseError(response);
  return response.status === 204
    ? (undefined as T)
    : (response.json() as Promise<T>);
}
export async function apiDownload(path: string) {
  const access = tokenStore.getAccessToken();
  const headers = new Headers(
    access ? { Authorization: `Bearer ${access}` } : {},
  );
  let response = await fetch(`${apiBaseUrl}${path}`, { headers });
  if (response.status === 401) {
    const next = await refreshAccessToken();
    if (next) {
      headers.set("Authorization", `Bearer ${next}`);
      response = await fetch(`${apiBaseUrl}${path}`, { headers });
    }
  }
  if (!response.ok) throw await parseError(response);
  return response.blob();
}
