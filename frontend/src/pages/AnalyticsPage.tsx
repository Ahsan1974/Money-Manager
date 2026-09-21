import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, Bar, BarChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { api } from "@/api/client";
import { StatCard } from "@/components/money/MoneyCard";
import { formatMoney, money } from "@/utils/money";
import { useAuth } from "@/stores/auth";
import { DashboardSkeleton } from "@/components/ui/states";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/primitives";

type Analytics = {
  income: string;
  expenses: string;
  saved: string;
  savings_rate: string;
  daily_average: string;
  highest_spending_day: { date: string | null; amount: string };
  largest_transaction: { merchant: string | null; amount: string };
  top_merchants: { merchant: string; total: string }[];
  categories: { name: string; total: string; color: string }[];
  income_trend: { label: string; amount: string }[];
  expense_trend: { label: string; amount: string }[];
  savings_trend: { label: string; amount: string }[];
  subscriptions: { monthly: string; annual: string; active: number };
};

export function AnalyticsPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data, isLoading } = useQuery({ queryKey: ["analytics"], queryFn: () => api<Analytics>("/api/analytics/") });
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => api<{ savings_rate: string; expense_growth: string; budget_adherence: string; emergency_reserve_progress: string; debt_ratio: string; recurring_expense_ratio: string; methodology: Record<string, string> }>("/api/analytics/health/"),
  });
  const navigate = useNavigate();
  if (isLoading || !data) return <DashboardSkeleton />;
  const trend = data.expense_trend.map((row, i) => ({
    label: row.label.slice(0, 3),
    expenses: money(row.amount),
    income: money(data.income_trend[i]?.amount),
    saved: money(data.savings_trend[i]?.amount),
  }));
  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Patterns</p>
          <h1 className="font-display text-3xl">Analytics</h1>
        </div>
        <Button variant="ghost" onClick={() => navigate("/app/yearly")}>
          Yearly
        </Button>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Income" value={formatMoney(data.income, symbol)} tone="good" />
        <StatCard label="Expenses" value={formatMoney(data.expenses, symbol)} />
        <StatCard label="Saved" value={formatMoney(data.saved, symbol)} />
        <StatCard label="Savings rate" value={`${data.savings_rate}%`} />
        <StatCard label="Daily average" value={formatMoney(data.daily_average, symbol)} />
        <StatCard label="Largest" value={formatMoney(data.largest_transaction.amount, symbol)} hint={data.largest_transaction.merchant || undefined} />
      </div>
      <div className="rounded-card border border-paper-line bg-paper-raised p-4 dark:border-[#2a2c2a] dark:bg-[#161816]">
        <h2 className="mb-3 font-medium">Income vs expenses</h2>
        <div className="h-48">
          <ResponsiveContainer>
            <BarChart data={trend}>
              <XAxis dataKey="label" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v: number) => formatMoney(v, symbol)} />
              <Bar dataKey="income" fill="#1F6B4A" radius={4} />
              <Bar dataKey="expenses" fill="#141413" radius={4} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="rounded-card border border-paper-line bg-paper-raised p-4 dark:border-[#2a2c2a] dark:bg-[#161816]">
        <h2 className="mb-3 font-medium">Savings</h2>
        <div className="h-40">
          <ResponsiveContainer>
            <AreaChart data={trend}>
              <XAxis dataKey="label" tick={{ fontSize: 10 }} hide />
              <Tooltip formatter={(v: number) => formatMoney(v, symbol)} />
              <Area dataKey="saved" stroke="#1F6B4A" fill="#1F6B4A22" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <section>
        <h2 className="mb-2 font-medium">Top merchants</h2>
        {data.top_merchants.map((row) => (
          <div key={row.merchant} className="flex justify-between py-2 text-sm">
            <span>{row.merchant}</span>
            <span className="tabular">{formatMoney(row.total, symbol)}</span>
          </div>
        ))}
      </section>
      {health && (
        <section className="space-y-2">
          <h2 className="font-medium">Health indicators</h2>
          <p className="text-xs text-ink-muted">Descriptive measures from your data — not a credit score or advice.</p>
          {[
            ["Savings rate", `${health.savings_rate}%`, health.methodology.savings_rate],
            ["Expense growth", `${health.expense_growth}%`, health.methodology.expense_growth],
            ["Budget adherence", `${health.budget_adherence}%`, health.methodology.budget_adherence],
            ["Emergency reserve", `${health.emergency_reserve_progress}%`, health.methodology.emergency_reserve_progress],
            ["Debt ratio", `${health.debt_ratio}%`, health.methodology.debt_ratio],
            ["Recurring share", `${health.recurring_expense_ratio}%`, health.methodology.recurring_expense_ratio],
          ].map(([label, value, method]) => (
            <div key={label} className="rounded-2xl border border-paper-line p-3 dark:border-[#2a2c2a]">
              <div className="flex justify-between text-sm">
                <span>{label}</span>
                <span className="tabular font-medium">{value}</span>
              </div>
              <p className="mt-1 text-xs text-ink-muted">{method}</p>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
