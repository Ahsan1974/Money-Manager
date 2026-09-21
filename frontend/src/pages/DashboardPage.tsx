import { useQuery } from "@tanstack/react-query";
import { Eye, EyeOff } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { format } from "date-fns";
import { api } from "@/api/client";
import { DashboardCharts } from "@/charts/DashboardCharts";
import { MoneyCard, StatCard } from "@/components/money/MoneyCard";
import { TransactionItem } from "@/components/money/TransactionItem";
import { BudgetProgress, GoalProgress } from "@/components/money/Progress";
import { CategoryIcon } from "@/components/money/CategoryIcon";
import { DashboardSkeleton } from "@/components/ui/states";
import { BottomSheet } from "@/components/ui/overlays";
import { formatMoney } from "@/utils/money";
import type { Dashboard } from "@/types";
import { useAuth } from "@/stores/auth";
import { useUI } from "@/stores/ui";
import { useState } from "react";

export function DashboardPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<Dashboard>("/api/dashboard/"),
  });
  const profile = useAuth((s) => s.profile);
  const hide = useUI((s) => s.hideBalance);
  const setHide = useUI((s) => s.setHideBalance);
  const setAddOpen = useUI((s) => s.setAddOpen);
  const navigate = useNavigate();
  const [stsOpen, setStsOpen] = useState(false);
  const symbol = data?.currency_symbol || profile?.currency_symbol || "Rs.";

  if (isLoading) return <DashboardSkeleton />;
  if (isError || !data) {
    return (
      <div className="py-16 text-center">
        <p>Something went wrong. Please try again.</p>
        <button className="mt-3 underline" onClick={() => refetch()}>
          Retry
        </button>
      </div>
    );
  }

  const hidden = hide || data.hide_balance;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-ink-muted">{format(new Date(data.date), "EEEE d MMMM")}</p>
          <h1 className="mt-1 font-display text-3xl tracking-tight">
            {data.greeting}, {data.display_name.split(" ")[0]}.
          </h1>
        </div>
        <button
          aria-label={hidden ? "Show balances" : "Hide balances"}
          className="rounded-full p-2"
          onClick={() => {
            const next = !hide;
            setHide(next);
            api("/api/auth/me/", { method: "PATCH", body: JSON.stringify({ hide_balance: next }) }).catch(() => undefined);
          }}
        >
          {hidden ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
        </button>
      </div>

      <MoneyCard
        label="Total balance"
        amount={data.total_balance}
        symbol={symbol}
        hidden={hidden}
        hint={`${Number(data.balance_change_percent) >= 0 ? "+" : ""}${data.balance_change_percent}% vs last month`}
      />

      <button
        onClick={() => setStsOpen(true)}
        className="w-full rounded-card border border-paper-line bg-paper-raised p-4 text-left dark:border-[#2a2c2a] dark:bg-[#161816]"
      >
        <p className="text-xs uppercase tracking-[0.18em] text-ink-muted">Safe to spend</p>
        <p className="tabular mt-2 text-3xl font-semibold text-forest">{formatMoney(data.safe_to_spend.safe_to_spend, symbol, hidden)}</p>
        <p className="mt-1 text-xs text-ink-muted">Available minus bills, debts, goals and reserves. Tap for breakdown.</p>
      </button>

      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Income" value={formatMoney(data.month_overview.income, symbol, hidden)} tone="good" />
        <StatCard label="Expenses" value={formatMoney(data.month_overview.expenses, symbol, hidden)} />
        <StatCard label="Saved" value={formatMoney(data.month_overview.saved, symbol, hidden)} tone="good" />
        <StatCard label="Savings rate" value={`${data.month_overview.savings_rate}%`} />
      </div>

      <div className="rounded-card border border-paper-line bg-paper-raised p-4 dark:border-[#2a2c2a] dark:bg-[#161816]">
        <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Today</p>
        <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
          <div>
            <p className="text-ink-muted">Spent</p>
            <p className="tabular font-semibold">{formatMoney(data.today.spent_today, symbol, hidden)}</p>
          </div>
          <div>
            <p className="text-ink-muted">Income</p>
            <p className="tabular font-semibold">{formatMoney(data.today.income_today, symbol, hidden)}</p>
          </div>
          <div>
            <p className="text-ink-muted">Daily left</p>
            <p className="tabular font-semibold">{formatMoney(data.today.remaining_daily_allowance, symbol, hidden)}</p>
          </div>
        </div>
      </div>

      <SpendingChart daily={data.spending_chart.daily} weekly={data.spending_chart.weekly} monthly={data.spending_chart.monthly} symbol={symbol} />

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-medium">Where it went</h2>
        </div>
        <div className="space-y-2">
          {data.categories.slice(0, 6).map((cat) => (
            <button
              key={String(cat.id) + cat.name}
              className="flex w-full items-center gap-3"
              onClick={() => navigate(`/app/transactions?category=${cat.id || ""}`)}
            >
              <CategoryIcon name={cat.icon} color={cat.color} />
              <div className="min-w-0 flex-1">
                <div className="flex justify-between text-sm">
                  <span>{cat.name}</span>
                  <span className="tabular">{formatMoney(cat.total, symbol, hidden)}</span>
                </div>
              </div>
            </button>
          ))}
          {!data.categories.length && <p className="text-sm text-ink-muted">No spending this month yet.</p>}
        </div>
      </section>

      {!!data.upcoming_bills.length && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-medium">Coming up</h2>
            <button className="text-sm text-ink-muted" onClick={() => navigate("/app/bills")}>
              All bills
            </button>
          </div>
          <div className="space-y-2">
            {data.upcoming_bills.map((bill) => (
              <div key={bill.id} className="flex items-center justify-between rounded-2xl border border-paper-line px-4 py-3 dark:border-[#2a2c2a]">
                <div>
                  <p className="font-medium">{bill.name}</p>
                  <p className="text-xs text-ink-muted">
                    {format(new Date(bill.due_date), "d MMM")} · {bill.status.replace("_", " ")}
                  </p>
                </div>
                <p className="tabular text-sm font-semibold">{formatMoney(bill.amount, symbol, hidden)}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {data.budgets?.items?.length ? (
        <section className="space-y-3">
          <h2 className="font-medium">Budgets</h2>
          {data.budgets.items.slice(0, 4).map((item) => (
            <button key={item.category_name} className="w-full text-left" onClick={() => navigate("/app/budgets")}>
              <div className="mb-1 flex justify-between text-sm">
                <span>{item.category_name}</span>
                <span className="tabular text-ink-muted">
                  {formatMoney(item.spent, symbol, hidden)} / {formatMoney(item.allocated, symbol, hidden)}
                </span>
              </div>
              <BudgetProgress percent={item.used_percent} color={item.category_color} />
            </button>
          ))}
        </section>
      ) : null}

      {!!data.goals.length && (
        <section>
          <h2 className="mb-3 font-medium">Goals</h2>
          <div className="flex gap-3 overflow-x-auto no-scrollbar">
            {data.goals.map((goal) => (
              <button
                key={goal.id}
                onClick={() => navigate("/app/goals")}
                className="min-w-[200px] rounded-card border border-paper-line bg-paper-raised p-4 text-left dark:border-[#2a2c2a] dark:bg-[#161816]"
              >
                <GoalProgress percent={goal.progress} color={goal.color} />
                <p className="mt-2 font-medium">{goal.name}</p>
                <p className="tabular text-xs text-ink-muted">
                  {formatMoney(goal.current_amount, symbol, hidden)} of {formatMoney(goal.target_amount, symbol, hidden)}
                </p>
              </button>
            ))}
          </div>
        </section>
      )}

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-medium">Recent</h2>
          <button className="text-sm text-ink-muted" onClick={() => navigate("/app/transactions")}>
            See all
          </button>
        </div>
        {data.recent_transactions.map((tx) => (
          <TransactionItem key={tx.id} tx={tx} symbol={symbol} onClick={() => navigate("/app/transactions")} />
        ))}
        {!data.recent_transactions.length && (
          <p className="text-sm text-ink-muted">
            Add your first transaction to start understanding your spending.{" "}
            <button className="underline" onClick={() => setAddOpen(true)}>
              Add transaction
            </button>
          </p>
        )}
      </section>

      {!!data.insights?.length && (
        <section className="space-y-2">
          <h2 className="font-medium">Insights</h2>
          {data.insights.slice(0, 3).map((insight) => (
            <div key={insight.id} className="rounded-2xl border border-paper-line p-4 dark:border-[#2a2c2a]">
              <p className="text-sm font-medium">{insight.title}</p>
              <p className="mt-1 text-sm text-ink-muted">{insight.body}</p>
            </div>
          ))}
        </section>
      )}

      <DashboardCharts
        categories={data.categories}
        income={data.month_overview.income}
        expenses={data.month_overview.expenses}
        saved={data.month_overview.saved}
        symbol={symbol}
      />

      <BottomSheet open={stsOpen} onClose={() => setStsOpen(false)} title="Safe to spend">
        <dl className="space-y-3 text-sm">
          {[
            ["Available", data.safe_to_spend.available],
            ["Upcoming bills", `-${data.safe_to_spend.upcoming_bills}`],
            ["Debt payments", `-${data.safe_to_spend.debt_payments}`],
            ["Goal reserve", `-${data.safe_to_spend.goal_reserve}`],
            ["Emergency reserve", `-${data.safe_to_spend.emergency_reserve}`],
            ["Savings reserve", `-${data.safe_to_spend.savings_reserve}`],
          ].map(([label, value]) => (
            <div key={label} className="flex justify-between">
              <dt className="text-ink-muted">{label}</dt>
              <dd className="tabular">{formatMoney(String(value).replace("-", ""), symbol, hidden)}</dd>
            </div>
          ))}
          <div className="flex justify-between border-t border-paper-line pt-3 font-semibold">
            <dt>Safe to spend</dt>
            <dd className="tabular text-forest">{formatMoney(data.safe_to_spend.safe_to_spend, symbol, hidden)}</dd>
          </div>
        </dl>
        <p className="mt-4 text-xs text-ink-muted">
          Configurable in Settings. This is a planning figure, not a financial guarantee.
        </p>
      </BottomSheet>
    </div>
  );
}
