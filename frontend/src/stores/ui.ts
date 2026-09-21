import { create } from "zustand";

type Toast = { id: number; message: string; tone?: "ok" | "error" };

type UIState = {
  addOpen: boolean;
  searchOpen: boolean;
  locked: boolean;
  toasts: Toast[];
  theme: "light" | "dark" | "system";
  hideBalance: boolean;
  setAddOpen: (open: boolean) => void;
  setSearchOpen: (open: boolean) => void;
  setLocked: (locked: boolean) => void;
  toast: (message: string, tone?: "ok" | "error") => void;
  dismiss: (id: number) => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
  setHideBalance: (hide: boolean) => void;
};

let toastId = 1;

export const useUI = create<UIState>((set, get) => ({
  addOpen: false,
  searchOpen: false,
  locked: false,
  toasts: [],
  theme: (localStorage.getItem("monea.theme") as UIState["theme"]) || "system",
  hideBalance: false,
  setAddOpen: (addOpen) => set({ addOpen }),
  setSearchOpen: (searchOpen) => set({ searchOpen }),
  setLocked: (locked) => set({ locked }),
  setHideBalance: (hideBalance) => set({ hideBalance }),
  toast: (message, tone = "ok") => {
    const id = toastId++;
    set({ toasts: [...get().toasts, { id, message, tone }] });
    window.setTimeout(() => get().dismiss(id), 3200);
  },
  dismiss: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
  setTheme: (theme) => {
    localStorage.setItem("monea.theme", theme);
    set({ theme });
    applyTheme(theme);
  },
}));

export function applyTheme(theme: "light" | "dark" | "system") {
  const dark =
    theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
  document.body.classList.toggle("bg-paper", !dark);
  document.body.classList.toggle("dark:bg-[#0c0d0c]", true);
}
