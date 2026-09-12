"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

export type UserRole = "mp" | "state_nodal" | "district" | "ministry";

export interface AuthUser {
  token: string;
  role: UserRole;
  scopeId: string | null;
  fullName: string;
  email: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  acceptInvite: (token: string, newPassword: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const STORAGE_KEY = "nirikshak_auth";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setUser(JSON.parse(raw));
    } catch {
      // localStorage unavailable (private mode, etc.) - stay logged out
    }
    setLoading(false);
  }, []);

  const applyAuthResponse = useCallback((data: any) => {
    const authUser: AuthUser = {
      token: data.access_token,
      role: data.role,
      scopeId: data.scope_id ?? null,
      fullName: data.full_name,
      email: data.email,
    };
    setUser(authUser);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(authUser));
    } catch {
      // best-effort persistence only
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || "Login failed");
    }
    applyAuthResponse(await res.json());
  }, [applyAuthResponse]);

  const acceptInvite = useCallback(async (token: string, newPassword: string) => {
    const res = await fetch("/api/auth/accept-invite", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || "Could not accept invite");
    }
    applyAuthResponse(await res.json());
  }, [applyAuthResponse]);

  const logout = useCallback(() => {
    setUser(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // no-op
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, acceptInvite, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

/** Attach the logged-in user's bearer token to a fetch call from a client component. */
export function withAuthHeader(user: AuthUser | null, headers: HeadersInit = {}): HeadersInit {
  if (!user) return headers;
  return { ...headers, Authorization: `Bearer ${user.token}` };
}

const ROLE_LABELS: Record<UserRole, string> = {
  mp: "Member of Parliament",
  state_nodal: "State Nodal Authority",
  district: "District Authority",
  ministry: "Ministry",
};

export function roleLabel(role: UserRole): string {
  return ROLE_LABELS[role] ?? role;
}

/** Redirects to /login if not authenticated; optionally restricts to specific roles. */
export function useRequireAuth(allowedRoles?: UserRole[]) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (allowedRoles && !allowedRoles.includes(user.role)) {
      router.replace("/overview");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, loading]);

  return { user, loading };
}
