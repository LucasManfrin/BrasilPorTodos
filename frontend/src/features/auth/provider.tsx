"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { ApiError, csrfCookie, fetchApi } from "@/lib/api";
import type { Envelope, User } from "@/lib/types";

type Credentials = { access_token: string; csrf_token: string; user: User };
let renewal: Promise<Envelope<Credentials>> | null = null;
function renew() {
  if (!renewal)
    renewal = fetchApi<Credentials>("auth/refresh", {
      method: "POST",
      headers: { "X-CSRF-Token": csrfCookie() },
    }).finally(() => {
      renewal = null;
    });
  return renewal;
}
type Auth = {
  user: User | null;
  loading: boolean;
  signIn: (
    mode: "login" | "register",
    values: Record<string, string>,
  ) => Promise<void>;
  signOut: () => Promise<void>;
  request: <T>(path: string, options?: RequestInit) => Promise<Envelope<T>>;
};
const AuthContext = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const token = useRef<string | null>(null);
  const apply = useCallback((values: Credentials) => {
    token.current = values.access_token;
    setUser(values.user);
  }, []);
  useEffect(() => {
    let active = true;
    async function restore() {
      try {
        if (csrfCookie()) {
          const result = await renew();
          if (active) apply(result.data);
        }
      } catch {
        if (active) {
          token.current = null;
          setUser(null);
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    void restore();
    return () => {
      active = false;
    };
  }, [apply]);
  const signIn = useCallback(
    async (mode: "login" | "register", values: Record<string, string>) => {
      const result = await fetchApi<Credentials>(`auth/${mode}`, {
        method: "POST",
        body: JSON.stringify(values),
      });
      apply(result.data);
    },
    [apply],
  );
  const signOut = useCallback(async () => {
    try {
      await fetchApi("auth/logout", {
        method: "POST",
        headers: { "X-CSRF-Token": csrfCookie() },
      });
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) throw error;
    }
    token.current = null;
    setUser(null);
  }, []);
  const request = useCallback(
    async <T,>(path: string, options: RequestInit = {}) => {
      try {
        return await fetchApi<T>(path, options, token.current);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401 && csrfCookie()) {
          try {
            const result = await renew();
            apply(result.data);
          } catch {
            token.current = null;
            setUser(null);
            throw error;
          }
          return fetchApi<T>(path, options, token.current);
        }
        throw error;
      }
    },
    [apply],
  );
  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut, request }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("AuthProvider is required.");
  return context;
}
