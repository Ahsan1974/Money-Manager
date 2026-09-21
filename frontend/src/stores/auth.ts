import { create } from "zustand";
import { api, tokens } from "@/api/client";
import type { Profile } from "@/types";

type AuthState = {
  profile: Profile | null;
  loading: boolean;
  hydrate: () => Promise<void>;
  logout: () => Promise<void>;
  setProfile: (profile: Profile) => void;
};

export const useAuth = create<AuthState>((set) => ({
  profile: null,
  loading: true,
  setProfile: (profile) => set({ profile }),
  hydrate: async () => {
    try {
      const profile = await api<Profile>("/api/auth/me/");
      set({ profile, loading: false });
    } catch {
      tokens.clear();
      try {
        const profile = await api<Profile>("/api/auth/me/", { skipAuth: true });
        set({ profile, loading: false });
      } catch {
        set({ profile: null, loading: false });
      }
    }
  },
  logout: async () => {
    tokens.clear();
    try {
      const profile = await api<Profile>("/api/auth/me/", { skipAuth: true });
      set({ profile });
    } catch {
      set({ profile: null });
    }
  },
}));
