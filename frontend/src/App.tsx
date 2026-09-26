import { Component, lazy, Suspense, type ReactNode, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { useAuth } from "@/stores/auth";
import { applyTheme, useUI } from "@/stores/ui";
import { flushOfflineQueue } from "@/api/client";

const TransactionsPage = lazy(() => import("@/pages/TransactionsPage").then((m) => ({ default: m.TransactionsPage })));
const AccountsPage = lazy(() => import("@/pages/AccountsPage").then((m) => ({ default: m.AccountsPage })));
const AccountDetailPage = lazy(() => import("@/pages/AccountDetailPage").then((m) => ({ default: m.AccountDetailPage })));
const BudgetsPage = lazy(() => import("@/pages/BudgetsPage").then((m) => ({ default: m.BudgetsPage })));
const GoalsPage = lazy(() => import("@/pages/GoalsPage").then((m) => ({ default: m.GoalsPage })));
const BillsPage = lazy(() => import("@/pages/BillsPage").then((m) => ({ default: m.BillsPage })));
const SubscriptionsPage = lazy(() => import("@/pages/SubscriptionsPage").then((m) => ({ default: m.SubscriptionsPage })));
const DebtsPage = lazy(() => import("@/pages/DebtsPage").then((m) => ({ default: m.DebtsPage })));
const LendingPage = lazy(() => import("@/pages/LendingPage").then((m) => ({ default: m.LendingPage })));
const AnalyticsPage = lazy(() => import("@/pages/AnalyticsPage").then((m) => ({ default: m.AnalyticsPage })));
const YearlyPage = lazy(() => import("@/pages/YearlyPage").then((m) => ({ default: m.YearlyPage })));
const NetWorthPage = lazy(() => import("@/pages/NetWorthPage").then((m) => ({ default: m.NetWorthPage })));
const InvestmentsPage = lazy(() => import("@/pages/InvestmentsPage").then((m) => ({ default: m.InvestmentsPage })));
const ReportsPage = lazy(() => import("@/pages/ReportsPage").then((m) => ({ default: m.ReportsPage })));
const ImportPage = lazy(() => import("@/pages/ImportPage").then((m) => ({ default: m.ImportPage })));
const SettingsPage = lazy(() => import("@/pages/SettingsPage").then((m) => ({ default: m.SettingsPage })));
const MorePage = lazy(() => import("@/pages/MorePage").then((m) => ({ default: m.MorePage })));
const AssistantPage = lazy(() => import("@/pages/AssistantPage").then((m) => ({ default: m.AssistantPage })));
const CalculatorPage = lazy(() => import("@/pages/CalculatorPage").then((m) => ({ default: m.CalculatorPage })));
const NotificationsPage = lazy(() => import("@/pages/NotificationsPage").then((m) => ({ default: m.NotificationsPage })));
const CategoriesPage = lazy(() => import("@/pages/CategoriesPage").then((m) => ({ default: m.CategoriesPage })));

const client = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 60_000 },
  },
});

function PageFallback() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center text-ink-muted">
      Loading…
    </div>
  );
}

class ErrorBoundary extends Component<{ children: ReactNode }, { message: string | null }> {
  state = { message: null as string | null };

  static getDerivedStateFromError(error: Error) {
    return { message: error.message || "Something went wrong." };
  }

  render() {
    if (this.state.message) {
      return (
        <div className="flex min-h-dvh flex-col items-center justify-center bg-[var(--bg)] px-6 text-center text-[var(--ink)]">
          <p className="font-display text-3xl">MONEA</p>
          <p className="mt-3 text-sm text-ink-muted">{this.state.message}</p>
          <button className="mt-4 underline" onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function Boot() {
  const { profile, hydrate } = useAuth();
  const setTheme = useUI((s) => s.setTheme);
  const setHide = useUI((s) => s.setHideBalance);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    const theme = profile?.theme || useUI.getState().theme;
    setTheme(theme);
    applyTheme(theme);
    if (profile) setHide(profile.hide_balance);
  }, [profile, setTheme, setHide]);

  useEffect(() => {
    applyTheme(useUI.getState().theme);
    const onOnline = () => flushOfflineQueue();
    window.addEventListener("online", onOnline);
    if (navigator.onLine) flushOfflineQueue();
    return () => window.removeEventListener("online", onOnline);
  }, []);

  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="accounts" element={<AccountsPage />} />
          <Route path="accounts/:id" element={<AccountDetailPage />} />
          <Route path="budgets" element={<BudgetsPage />} />
          <Route path="goals" element={<GoalsPage />} />
          <Route path="bills" element={<BillsPage />} />
          <Route path="subscriptions" element={<SubscriptionsPage />} />
          <Route path="debts" element={<DebtsPage />} />
          <Route path="lending" element={<LendingPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="yearly" element={<YearlyPage />} />
          <Route path="net-worth" element={<NetWorthPage />} />
          <Route path="investments" element={<InvestmentsPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="import" element={<ImportPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="more" element={<MorePage />} />
          <Route path="assistant" element={<AssistantPage />} />
          <Route path="calculator" element={<CalculatorPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="categories" element={<CategoriesPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <ErrorBoundary>
          <Boot />
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
