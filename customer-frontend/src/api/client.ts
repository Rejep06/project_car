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

async function parseError(response: Response): Promise<ApiClientError> {
  try {
    const body = (await response.json()) as { error?: ApiError };
    if (body.error) return new ApiClientError(body.error, response.status);
  } catch {
    // Сервер мог вернуть пустое тело; ниже используется безопасное сообщение.
  }
  return new ApiClientError(
    { code: "http_error", message: `Ошибка HTTP ${response.status}` },
    response.status,
  );
}

async function requestNewAccessToken(
  refreshToken: string,
): Promise<string | null> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    // Временная ошибка сети не должна уничтожать сохранённую сессию.
    return null;
  }

  if (!response.ok) {
    const latestRefreshToken = tokenStore.getRefreshToken();

    // Другая вкладка могла уже обновить пару токенов.
    if (latestRefreshToken && latestRefreshToken !== refreshToken) {
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

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = tokenStore.getRefreshToken();
  if (!refreshToken) return null;

  if (!refreshPromise) {
    refreshPromise = requestNewAccessToken(refreshToken).finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  skipRefresh?: boolean;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { skipAuth = false, skipRefresh = false, ...fetchOptions } = options;
  const headers = new Headers(fetchOptions.headers);
  const bodyIsForm = fetchOptions.body instanceof FormData;
  if (fetchOptions.body && !bodyIsForm && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const access = tokenStore.getAccessToken();
  if (!skipAuth && access) headers.set("Authorization", `Bearer ${access}`);

  let response = await fetch(`${apiBaseUrl}${path}`, {
    ...fetchOptions,
    headers,
  });
  if (response.status === 401 && !skipAuth && !skipRefresh) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${refreshed}`);
      response = await fetch(`${apiBaseUrl}${path}`, {
        ...fetchOptions,
        headers,
      });
    }
  }
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function apiDownload(path: string): Promise<Blob> {
  const access = tokenStore.getAccessToken();
  const headers = new Headers();
  if (access) headers.set("Authorization", `Bearer ${access}`);
  let response = await fetch(`${apiBaseUrl}${path}`, { headers });
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${refreshed}`);
      response = await fetch(`${apiBaseUrl}${path}`, { headers });
    }
  }
  if (!response.ok) throw await parseError(response);
  return response.blob();
}

export { apiBaseUrl, refreshAccessToken };
