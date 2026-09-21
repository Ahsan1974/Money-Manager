import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { formatMoney, money } from "@/utils/money";
import { useNavigate } from "react-router-dom";
import type { SafeToSpend } from "@/types";

type Slice = { name: string; value: number; color: string; href?: string };

function Donut({
  title,
  subtitle,
  data,
  symbol,
  empty,
}: {
  title: string;
  subtitle?: string;
  data: Slice[];
  symbol: string;
  empty: string;
}) {
  const navigate = useNavigate();
  const total = data.reduce((sum, row) => sum + row.value, 0);
  return (
    <div className="rounded-card border border-paper-line bg-paper-raised p-4 dark:border-[#2a2c2a] dark:bg-[#161816]">
      <h3 className="font-medium">{title}</h3>
      {subtitle && <p className="mt-1 text-xs text-ink-muted">{subtitle}</p>}
      {!data.length || total <= 0 ? (
        <p className="py-10 text-center text-sm text-ink-muted">{empty}</p>
      ) : (
        <div className="mt-2 grid grid-cols-[140px_1fr] items-center gap-2">
          <div className="h-36">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={data} dataKey="value" nameKey="name" innerRadius={42} outerRadius={64} paddingAngle={2} stroke="none">
                  {data.map((row) => (
                    <Cell
                      key={row.name}
                      fill={row.color}
                      cursor={row.href ? "pointer" : "default"}
                      onClick={() => row.href && navigate(row.href)}
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatMoney(value, symbol)} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="space-y-1.5 text-sm">
            {data.map((row) => (
              <li key={row.name}>
                <button
                  type="button"
                  className="flex w-full items-center justify-between gap-2 text-left"
                  onClick={() => row.href && navigate(row.href)}
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: row.color }} />
                    <span className="truncate">{row.name}</span>
                  </span>
                  <span className="tabular shrink-0 text-ink-muted">{formatMoney(row.value, symbol)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

const PALETTE = ["#1F6B4A", "#141413", "#C4B5A5", "#6B8F71", "#8B6F47", "#3D5A4A", "#A67C52", "#2C3E50"];

export function DashboardCharts({
  categories,
  income,
  expenses,
  saved,
  accounts,
  safeToSpend,
  assets,
  liabilities,
  symbol,
}: {
  categories: { id: number | null; name: string; color: string; total: string }[];
  income: string;
  expenses: string;
  saved: string;
  accounts: { id: number; name: string; balance: string; color: string; is_liability: boolean }[];
  safeToSpend: SafeToSpend;
  assets: string;
  liabilities: string;
  symbol: string;
}) {
  const categorySlices = categories
    .map((row, index) => ({
      name: row.name,
      value: money(row.total),
      color: row.color || PALETTE[index % PALETTE.length],
      href: `/app/transactions?category=${row.id || ""}`,
    }))
    .filter((row) => row.value > 0)
    .slice(0, 8);

  const flow = [
    { name: "Income", value: money(income), color: "#1F6B4A" },
    { name: "Expenses", value: money(expenses), color: "#141413" },
    { name: "Saved", value: Math.max(money(saved), 0), color: "#C4B5A5" },
  ].filter((row) => row.value > 0);

  const accountSlices = accounts
    .map((row, index) => ({
      name: row.name,
      value: Math.abs(money(row.balance)),
      color: row.color || PALETTE[index % PALETTE.length],
      href: "/app/accounts",
    }))
    .filter((row) => row.value > 0);

  const obligationSlices = [
    { name: "Safe to spend", value: Math.max(money(safeToSpend.safe_to_spend), 0), color: "#1F6B4A" },
    { name: "Bills", value: money(safeToSpend.upcoming_bills), color: "#141413", href: "/app/bills" },
    { name: "Debts", value: money(safeToSpend.debt_payments), color: "#8B6F47", href: "/app/debts" },
    { name: "Goals", value: money(safeToSpend.goal_reserve), color: "#6B8F71", href: "/app/goals" },
    { name: "Emergency", value: money(safeToSpend.emergency_reserve), color: "#C4B5A5" },
    { name: "Savings hold", value: money(safeToSpend.savings_reserve), color: "#3D5A4A" },
  ].filter((row) => row.value > 0);

  const netWorthSlices = [
    { name: "Assets", value: money(assets), color: "#1F6B4A", href: "/app/accounts" },
    { name: "Liabilities", value: money(liabilities), color: "#141413", href: "/app/debts" },
  ].filter((row) => row.value > 0);

  return (
    <section className="space-y-3">
      <h2 className="font-medium">This month at a glance</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <Donut
          title="Spending by category"
          subtitle="Tap a slice to open those transactions."
          data={categorySlices}
          symbol={symbol}
          empty="Add expenses to see a category breakdown."
        />
        <Donut
          title="Income, spending, saved"
          data={flow}
          symbol={symbol}
          empty="Log income or expenses to see this mix."
        />
        <Donut
          title="Where your money sits"
          subtitle="Balances across your accounts."
          data={accountSlices}
          symbol={symbol}
          empty="Add an account to see where the money lives."
        />
        <Donut
          title="Spoken for vs free"
          subtitle="How Safe to Spend is carved up."
          data={obligationSlices}
          symbol={symbol}
          empty="Add balances and bills to see this split."
        />
        <Donut
          title="Net worth mix"
          data={netWorthSlices}
          symbol={symbol}
          empty="Add assets or debts to see net worth."
        />
      </div>
    </section>
  );
}
