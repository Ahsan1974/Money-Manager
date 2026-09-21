import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  Bell,
  CreditCard,
  Flag,
  Home,
  Landmark,
  Menu,
  MoreHorizontal,
  PieChart,
  Plus,
  Repeat,
  Search,
  Settings,
  Target,
  Wallet,
  Handshake,
  Calculator,
  Sparkles,
  FileText,
  TrendingUp,
} from "lucide-react";
import { useEffect, useState } from "react";
import { AddSheet } from "@/features/transactions/AddSheet";
import { ToastHost } from "@/components/ui/overlays";
import { useUI } from "@/stores/ui";
import { useAuth } from "@/stores/auth";
import { cn } from "@/utils/cn";
import { SearchOverlay } from "@/components/layout/SearchOverlay";
import { PinLock } from "@/components/layout/PinLock";

const DESKTOP = [
  { to: "/app", label: "Dashboard", icon: Home, end: true },
  { to: "/app/transactions", label: "Transactions", icon: Wallet },
  { to: "/app/accounts", label: "Accounts", icon: Landmark },
  { to: "/app/budgets", label: "Budgets", icon: PieChart },
  { to: "/app/goals", label: "Goals", icon: Target },
  { to: "/app/bills", label: "Bills", icon: FileText },
  { to: "/app/subscriptions", label: "Subscriptions", icon: Repeat },
  { to: "/app/debts", label: "Debts", icon: CreditCard },
  { to: "/app/lending", label: "Lending", icon: Handshake },
  { to: "/app/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/app/reports", label: "Reports", icon: TrendingUp },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

const MOBILE = [
  { to: "/app", label: "Home", icon: Home, end: true },
  { to: "/app/transactions", label: "Activity", icon: Wallet },
  { to: "__add__", label: "Add", icon: Plus },
  { to: "/app/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/app/more", label: "More", icon: MoreHorizontal },
];

export function AppLayout() {
  const addOpen = useUI((s) => s.addOpen);
  const setAddOpen = useUI((s) => s.setAddOpen);
  const setSearchOpen = useUI((s) => s.setSearchOpen);
  const location = useLocation();
  const navigate = useNavigate();
  const profile = useAuth((s) => s.profile);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "/" && !(e.target instanceof HTMLInputElement) && !(e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setSearchOpen]);

  return (
    <div className="min-h-dvh bg-[var(--bg)] text-[var(--ink)]">
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-paper-line bg-paper-raised px-4 py-6 dark:border-[#2a2c2a] dark:bg-[#121412] lg:flex lg:flex-col">
        <div className="px-2">
          <p className="font-display text-3xl tracking-tight">MONEA</p>
          <p className="mt-1 text-[11px] uppercase tracking-[0.22em] text-ink-muted">Personal Finance OS</p>
        </div>
        <nav className="mt-8 flex-1 space-y-1 overflow-y-auto">
          {DESKTOP.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm",
                  isActive ? "bg-paper dark:bg-[#1b1d1b]" : "text-ink-muted hover:bg-paper/70 dark:hover:bg-[#1b1d1b]",
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={() => navigate("/app/assistant")}
          className="mt-3 flex items-center gap-2 rounded-2xl px-3 py-2 text-sm text-ink-muted"
        >
          <Sparkles className="h-4 w-4" />
          Assistant
        </button>
      </aside>

      <div className="lg:pl-60">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-transparent bg-[var(--bg)]/90 px-4 py-3 backdrop-blur lg:px-8">
          <div className="lg:hidden">
            <p className="font-display text-2xl leading-none">MONEA</p>
          </div>
          <div className="hidden lg:block">
            <p className="text-sm text-ink-muted">Private workspace</p>
          </div>
          <div className="flex items-center gap-1">
            <button aria-label="Search" className="rounded-full p-2" onClick={() => setSearchOpen(true)}>
              <Search className="h-5 w-5" />
            </button>
            <button aria-label="Notifications" className="rounded-full p-2" onClick={() => navigate("/app/notifications")}>
              <Bell className="h-5 w-5" />
            </button>
            <button
              aria-label="Profile"
              className="ml-1 flex h-8 w-8 items-center justify-center rounded-full bg-ink text-xs text-paper-raised"
              onClick={() => navigate("/app/settings")}
            >
              {(profile?.display_name || "M").slice(0, 1)}
            </button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-5xl px-4 pb-28 pt-2 lg:px-8 lg:pb-12">
          <Outlet key={location.pathname} />
        </main>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-paper-line bg-paper-raised/95 px-2 pb-[env(safe-area-inset-bottom)] pt-2 backdrop-blur dark:border-[#2a2c2a] dark:bg-[#121412]/95 lg:hidden">
        <div className="grid grid-cols-5 items-end">
          {MOBILE.map((item) =>
            item.to === "__add__" ? (
              <button
                key="add"
                aria-label="Add transaction"
                onClick={() => setAddOpen(true)}
                className="-mt-6 flex flex-col items-center"
              >
                <span className="flex h-14 w-14 items-center justify-center rounded-full bg-ink text-paper-raised shadow-card dark:bg-forest-dark">
                  <Plus className="h-6 w-6" />
                </span>
                <span className="mt-1 text-[10px] text-ink-muted">Add</span>
              </button>
            ) : (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn("flex flex-col items-center gap-1 py-1 text-[10px]", isActive ? "text-ink" : "text-ink-muted")
                }
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </NavLink>
            ),
          )}
        </div>
      </nav>

      <AddSheet open={addOpen} onClose={() => setAddOpen(false)} />
      <SearchOverlay />
      <PinLock />
      <ToastHost />
    </div>
  );
}
