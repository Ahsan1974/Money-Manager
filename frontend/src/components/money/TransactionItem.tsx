import { format } from "date-fns";
import { formatMoney } from "@/utils/money";
import type { Transaction } from "@/types";
import { CategoryIcon } from "@/components/money/CategoryIcon";
import { cn } from "@/utils/cn";

export function TransactionItem({
  tx,
  symbol,
  onClick,
  onEdit,
  onDelete,
}: {
  tx: Transaction;
  symbol?: string;
  onClick?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}) {
  const income = tx.transaction_type === "income";
  const transfer = tx.transaction_type === "transfer";
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center gap-3 rounded-2xl px-1 py-2 text-left active:bg-paper dark:active:bg-[#1b1d1b]"
    >
      <CategoryIcon name={tx.category_icon} color={tx.category_color} />
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{tx.merchant || tx.description || "Transaction"}</p>
        <p className="truncate text-xs text-ink-muted">
          {tx.category_name || (transfer ? "Transfer" : "Uncategorized")} · {tx.account_name} ·{" "}
          {format(new Date(tx.transaction_date), "d MMM")}
        </p>
      </div>
      <p className={cn("tabular text-sm font-semibold", income && "text-forest", !income && !transfer && "text-ink")}>
        {income ? "+" : transfer ? "" : "−"}
        {formatMoney(tx.amount, symbol)}
      </p>
      {(onEdit || onDelete) && (
        <span className="sr-only">
          {onEdit ? "Edit" : ""} {onDelete ? "Delete" : ""}
        </span>
      )}
    </button>
  );
}
