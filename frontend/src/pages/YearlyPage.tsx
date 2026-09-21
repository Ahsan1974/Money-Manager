import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { formatMoney } from "@/utils/money";
import { StatCard } from "@/components/money/MoneyCard";
import { useAuth } from "@/stores/auth";
import { DashboardSkeleton } from "@/components/ui/states";

type Review = {
  year: number;
  title: string;
  total_income: string;
  total_expenses: string;
  total_saved: string;
  savings_rate: string;
  average_monthly_income: string;
  average_monthly_expenses: string;
  largest_category: string | null;
  largest_expense: string | null;
  net_worth_change: string;
};

export function YearlyPage() {
  const year = new Date().getFullYear();
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data, isLoading } = useQuery({ queryKey: ["yearly", year], queryFn: () => api<Review>(`/api/analytics/yearly/?year=${year}`) });
  if (isLoading || !data) return <DashboardSkeleton />;
  return (
    <div className="space-y-5">
      <p className="font-display text-4xl leading-tight">{data.title}</p>
      <div className="grid grid-cols-1 gap-3">
        <StatCard label="Total income" value={formatMoney(data.total_income, symbol)} tone="good" />
        <StatCard label="Total expenses" value={formatMoney(data.total_expenses, symbol)} />
        <StatCard label="Total saved" value={formatMoney(data.total_saved, symbol)} />
        <StatCard label="Savings rate" value={`${data.savings_rate}%`} />
        <StatCard label="Avg monthly income" value={formatMoney(data.average_monthly_income, symbol)} />
        <StatCard label="Avg monthly expenses" value={formatMoney(data.average_monthly_expenses, symbol)} />
        <StatCard label="Largest category" value={data.largest_category || "—"} />
        <StatCard label="Largest expense" value={data.largest_expense || "—"} />
        <StatCard label="Net worth change" value={formatMoney(data.net_worth_change, symbol)} tone="good" />
      </div>
    </div>
  );
}
