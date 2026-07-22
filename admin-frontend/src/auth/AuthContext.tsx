import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import * as authApi from "../api/auth";
import type { User } from "../api/types";
import { getMe } from "../api/users";
import { tokenStore } from "./tokenStore";

interface AuthValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAdmin = useCallback(async () => {
    const current = await getMe();
    if (current.role !== "admin") {
      tokenStore.clear();
      setUser(null);
      throw new Error("Эта учётная запись не имеет роли администратора");
    }
    setUser(current);
    return current;
  }, []);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      const hasAccessToken = Boolean(tokenStore.getAccessToken());
      const hasRefreshToken = Boolean(tokenStore.getRefreshToken());

      if (!hasAccessToken && !hasRefreshToken) {
        if (active) setLoading(false);
        return;
      }

      try {
        // getMe сам обновит access token через refresh token при ответе 401.
        const current = await getMe();
        if (current.role === "admin") {
          if (active) setUser(current);
        } else {
          tokenStore.clear();
          if (active) setUser(null);
        }
      } catch {
        // Невалидный refresh token уже очищается в API-клиенте.
        if (active) setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    }

    void restoreSession();
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const pair = await authApi.login(email, password);
      tokenStore.setTokens(pair.access_token, pair.refresh_token);
      return loadAdmin();
    },
    [loadAdmin],
  );

  const logout = useCallback(async () => {
    const refresh = tokenStore.getRefreshToken();
    tokenStore.clear();
    setUser(null);
    if (refresh) {
      try {
        await authApi.logout(refresh);
      } catch {
        /* Локальная сессия уже завершена. */
      }
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout }),
    [user, loading, login, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value)
    throw new Error("useAuth должен использоваться внутри AuthProvider");
  return value;
}
