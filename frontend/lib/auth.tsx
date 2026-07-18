"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api, tokenStore } from "@/lib/api";
import type { AuthResponse, User, UserRole } from "@/types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string, remember?: boolean) => Promise<void>;
  register: (payload: { email: string; full_name: string; password: string; role: UserRole }, remember?: boolean) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function saveSession(result: AuthResponse, remember: boolean) {
  tokenStore.set(result.access_token, remember);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = tokenStore.get();
    if (!token) {
      Promise.resolve().then(() => setLoading(false));
      return;
    }
    api.me().then(setUser).catch(() => tokenStore.clear()).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const invalidate = () => setUser(null);
    window.addEventListener("startup-lens-auth-invalidated", invalidate);
    return () => window.removeEventListener("startup-lens-auth-invalidated", invalidate);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email, password, remember = true) => {
        const result = await api.login(email, password);
        saveSession(result, remember);
        setUser(result.user);
      },
      register: async (payload, remember = true) => {
        const result = await api.register(payload);
        saveSession(result, remember);
        setUser(result.user);
      },
      logout: () => {
        tokenStore.clear();
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
