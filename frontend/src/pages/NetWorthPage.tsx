import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { api } from "@/api/client";
import { formatMoney, money } from "@/utils/money";
import { StatCard } from "@/components/money/MoneyCard";
import { useAuth } from "@/stores/auth";

type NW = {
  assets: string;
  liabilities: string;
  net_worth: string;
  breakdown: { assets: { name: string; amount: string }[]; liabilities: { name: string; amount: string }[] };
  history: { date: string; net_worth: string }[];
};

export function NetWorthPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data } = useQuery({ queryKey: ["net-worth"], queryFn: () => api<NW>("/api/net-worth/") });
  if (!data) return <p className="text-sm text-ink-muted">Loading…</p>;
  const chart = data.history.map((row) => ({ label: row.date.slice(5), amount: money(row.net_worth) }));
  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Assets − liabilities</p>
        <h1 className="font-display text-3xl">Net worth</h1>
        <p className="tabular mt-3 text-4xl font-semibold">{formatMoney(data.net_worth, symbol)}</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Assets" value={formatMoney(data.assets, symbol)} tone="good" />
        <StatCard label="Liabilities" value={formatMoney(data.liabilities, symbol)} />
      </div>
      <div className="h-44 rounded-card border border-paper-line bg-paper-raised p-3 dark:border-[#2a2c2a] dark:bg-[#161816]">
        <ResponsiveContainer>
          <AreaChart data={chart}>
            <XAxis dataKey="label" tick={{ fontSize: 10 }} />
            <Tooltip formatter={(v: number) => formatMoney(v, symbol)} />
            <Area dataKey="amount" stroke="#1F6B4A" fill="#1F6B4A22" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <section>
        <h2 className="mb-2 font-medium">Assets</h2>
        {data.breakdown.assets.map((row) => (
          <div key={row.name} className="flex justify-between py-1 text-sm">
            <span>{row.name}</span>
            <span className="tabular">{formatMoney(row.amount, symbol)}</span>
          </div>
        ))}
      </section>
      <section>
        <h2 className="mb-2 font-medium">Liabilities</h2>
        {data.breakdown.liabilities.map((row) => (
          <div key={row.name} className="flex justify-between py-1 text-sm">
            <span>{row.name}</span>
            <span className="tabular">{formatMoney(row.amount, symbol)}</span>
          </div>
        ))}
      </section>
    </div>
  );
}
