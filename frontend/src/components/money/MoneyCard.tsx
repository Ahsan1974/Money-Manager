import { formatMoney } from "@/utils/money";
import { cn } from "@/utils/cn";

export function MoneyCard({
  label,
  amount,
  hint,
  symbol,
  hidden,
  onClick,
  className,
}: {
  label: string;
  amount: string | number;
  hint?: string;
  symbol?: string;
  hidden?: boolean;
  onClick?: () => void;
  className?: string;
}) {
  const Comp = onClick ? "button" : "div";
  return (
    <Comp
      onClick={onClick}
      className={cn(
        "w-full rounded-card bg-ink p-5 text-left text-paper-raised shadow-card dark:bg-[#121412]",
        className,
      )}
    >
      <p className="text-xs uppercase tracking-[0.18em] text-white/55">{label}</p>
      <p className="tabular mt-3 text-4xl font-semibold">{formatMoney(amount, symbol, hidden)}</p>
      {hint && <p className="mt-2 text-sm text-white/60">{hint}</p>}
    </Comp>
  );
}

export function StatCard({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "neutral" | "good" | "bad";
}) {
  return (
    <div className="rounded-card border border-paper-line bg-paper-raised p-4 dark:border-[#2a2c2a] dark:bg-[#161816]">
      <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">{label}</p>
      <p
        className={cn(
          "tabular mt-2 text-xl font-semibold",
          tone === "good" && "text-forest",
          tone === "bad" && "text-rose",
        )}
      >
        {value}
      </p>
      {hint && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
    </div>
  );
}
