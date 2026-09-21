import { Component, type ReactNode, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { TransactionsPage } from "@/pages/TransactionsPage";
import { AccountsPage } from "@/pages/AccountsPage";
import { AccountDetailPage } from "@/pages/AccountDetailPage";
import { BudgetsPage } from "@/pages/BudgetsPage";
import { GoalsPage } from "@/pages/GoalsPage";
import { BillsPage } from "@/pages/BillsPage";
import { SubscriptionsPage } from "@/pages/SubscriptionsPage";
import { DebtsPage } from "@/pages/DebtsPage";
import { LendingPage } from "@/pages/LendingPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { YearlyPage } from "@/pages/YearlyPage";
import { NetWorthPage } from "@/pages/NetWorthPage";
import { InvestmentsPage } from "@/pages/InvestmentsPage";
import { ReportsPage } from "@/pages/ReportsPage";
import { ImportPage } from "@/pages/ImportPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { MorePage } from "@/pages/MorePage";
import { AssistantPage } from "@/pages/AssistantPage";
import { CalculatorPage } from "@/pages/CalculatorPage";
import { NotificationsPage } from "@/pages/NotificationsPage";
import { CategoriesPage } from "@/pages/CategoriesPage";
import { useAuth } from "@/stores/auth";
import { applyTheme, useUI } from "@/stores/ui";
import { flushOfflineQueue } from "@/api/client";

const client = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

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
