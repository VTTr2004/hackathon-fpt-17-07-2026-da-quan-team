"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { AuthResponse, User, UserRole } from "@/types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: { email: string; full_name: string; password: string; role: UserRole }) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function saveSession(result: AuthResponse) {
  window.localStorage.setItem("startup_lens_token", result.access_token);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = window.localStorage.getItem("startup_lens_token");
    if (!token) {
      Promise.resolve().then(() => setLoading(false));
      return;
    }
    api.me().then(setUser).catch(() => window.localStorage.removeItem("startup_lens_token")).finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email, password) => {
        const result = await api.login(email, password);
        saveSession(result);
        setUser(result.user);
      },
      register: async (payload) => {
        const result = await api.register(payload);
        saveSession(result);
        setUser(result.user);
      },
      logout: () => {
        window.localStorage.removeItem("startup_lens_token");
        setUser(null);
        window.location.href = "/login";
      },
    }),
    [loading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
