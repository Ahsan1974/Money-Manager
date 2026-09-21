import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useEffect } from "react";
import { AppLayout } from "@/layouts/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
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

function Guard({ children }: { children: React.ReactNode }) {
  const { profile, loading, hydrate } = useAuth();
  useEffect(() => {
    hydrate();
  }, [hydrate]);
  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-[var(--bg)]">
        <p className="font-display text-3xl">MONEA</p>
      </div>
    );
  }
  if (!profile) return <Navigate to="/login" replace />;
  return children;
}

function Boot() {
  const profile = useAuth((s) => s.profile);
  const setTheme = useUI((s) => s.setTheme);
  const setHide = useUI((s) => s.setHideBalance);
  useEffect(() => {
    const theme = profile?.theme || useUI.getState().theme;
    setTheme(theme);
    applyTheme(theme);
    if (profile) setHide(profile.hide_balance);
  }, [profile, setTheme, setHide]);
  useEffect(() => {
    const onOnline = () => flushOfflineQueue();
    window.addEventListener("online", onOnline);
    if (navigator.onLine) flushOfflineQueue();
    return () => window.removeEventListener("online", onOnline);
  }, []);
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/app"
        element={
          <Guard>
            <AppLayout />
          </Guard>
        }
      >
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
        <Boot />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
