import { create } from "zustand";
import { api, tokens } from "@/api/client";
import type { Profile } from "@/types";

type AuthState = {
  profile: Profile | null;
  loading: boolean;
  hydrate: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  setProfile: (profile: Profile) => void;
};

export const useAuth = create<AuthState>((set) => ({
  profile: null,
  loading: true,
  setProfile: (profile) => set({ profile }),
  hydrate: async () => {
    if (!tokens.access()) {
      set({ loading: false, profile: null });
      return;
    }
    try {
      const profile = await api<Profile>("/api/auth/me/");
      set({ profile, loading: false });
    } catch {
      tokens.clear();
      set({ profile: null, loading: false });
    }
  },
  login: async (username, password) => {
    const data = await api<{ access: string; refresh: string }>("/api/auth/login/", {
      method: "POST",
      skipAuth: true,
      body: JSON.stringify({ username, password, remember: true }),
    });
    tokens.set(data.access, data.refresh);
    const profile = await api<Profile>("/api/auth/me/");
    set({ profile });
  },
  register: async (username, password, displayName) => {
    const data = await api<{ access: string; refresh: string }>("/api/auth/register/", {
      method: "POST",
      skipAuth: true,
      body: JSON.stringify({ username, password, display_name: displayName }),
    });
    tokens.set(data.access, data.refresh);
    const profile = await api<Profile>("/api/auth/me/");
    set({ profile });
  },
  logout: async () => {
    try {
      await api("/api/auth/logout/", { method: "POST", body: JSON.stringify({ refresh: localStorage.getItem("monea.refresh") }) });
    } catch {
      /* still sign out locally */
    }
    tokens.clear();
    set({ profile: null });
  },
}));
