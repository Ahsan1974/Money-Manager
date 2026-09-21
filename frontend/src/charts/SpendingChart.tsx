import { useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatMoney, money } from "@/utils/money";

export function SpendingChart({
  daily,
  weekly,
  monthly,
  symbol,
}: {
  daily: { date: string; amount: string }[];
  weekly: { label: string; amount: string }[];
  monthly: { label: string; amount: string }[];
  symbol: string;
}) {
  const [mode, setMode] = useState<"daily" | "weekly" | "monthly">("daily");
  const source = mode === "daily" ? daily : mode === "weekly" ? weekly : monthly;
  const data = source.map((row) => ({
    label: "date" in row ? String(row.date).slice(8) : row.label,
    amount: money((row as { amount: string }).amount),
  }));
  return (
    <div className="rounded-card border border-paper-line bg-paper-raised p-4 dark:border-[#2a2c2a] dark:bg-[#161816]">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-medium">Spending</h3>
        <div className="flex rounded-full bg-paper p-1 text-xs dark:bg-[#0c0d0c]">
          {(["daily", "weekly", "monthly"] as const).map((item) => (
            <button
              key={item}
              onClick={() => setMode(item)}
              className={`rounded-full px-3 py-1 capitalize ${mode === item ? "bg-paper-raised shadow-sm dark:bg-[#161816]" : "text-ink-muted"}`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>
      <div className="h-44">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="spend" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1F6B4A" stopOpacity={0.28} />
                <stop offset="100%" stopColor="#1F6B4A" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="label" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip
              formatter={(value: number) => formatMoney(value, symbol)}
              contentStyle={{ borderRadius: 12, border: "1px solid #E4DED4", fontSize: 12 }}
            />
            <Area type="monotone" dataKey="amount" stroke="#1F6B4A" strokeWidth={2} fill="url(#spend)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
