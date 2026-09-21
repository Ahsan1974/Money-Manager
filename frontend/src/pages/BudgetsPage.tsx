import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { BudgetProgress } from "@/components/money/Progress";
import { EmptyState } from "@/components/ui/states";
import { AmountInput, Button, Field, Select } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import { formatMoney } from "@/utils/money";
import type { Category } from "@/types";
import { useAuth } from "@/stores/auth";

type BudgetCurrent = {
  items: {
    id: number;
    category: number;
    category_name: string;
    category_color: string;
    allocated: string;
    spent: string;
    remaining: string;
    used_percent: string;
    days_remaining: number;
    projected: string;
    insight: string;
  }[];
};

export function BudgetsPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data } = useQuery({ queryKey: ["budgets-current"], queryFn: () => api<BudgetCurrent>("/api/budgets/current/") });
  const { data: categories } = useQuery({ queryKey: ["categories"], queryFn: () => api<Category[]>("/api/categories/") });
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState("");
  const [amount, setAmount] = useState("");
  const qc = useQueryClient();
  const now = new Date();
  const save = useMutation({
    mutationFn: async () => {
      const existing = await api<{ results: { id: number; items: unknown[] }[] }>(`/api/budgets/?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
      const current = existing.results?.[0];
      const items = [...((data?.items || []).map((item) => ({ category: item.category, allocated_amount: item.allocated })) ), { category: Number(category), allocated_amount: amount }];
      if (current) {
        return api(`/api/budgets/${current.id}/`, {
          method: "PATCH",
          body: JSON.stringify({ name: "Monthly budget", year: now.getFullYear(), month: now.getMonth() + 1, items }),
        });
      }
      return api("/api/budgets/", {
        method: "POST",
        body: JSON.stringify({ name: "Monthly budget", year: now.getFullYear(), month: now.getMonth() + 1, items }),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["budgets-current"] });
      setOpen(false);
    },
  });

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">This month</p>
          <h1 className="font-display text-3xl">Budgets</h1>
        </div>
        <Button onClick={() => setOpen(true)}>Add</Button>
      </div>
      {!data?.items?.length && (
        <EmptyState title="No budgets yet" body="Give each category a monthly ceiling so overspending is visible early." action="Create budget" onAction={() => setOpen(true)} />
      )}
      <div className="space-y-5">
        {data?.items.map((item) => (
          <div key={item.id}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="font-medium">{item.category_name}</span>
              <span className="tabular text-ink-muted">
                {formatMoney(item.spent, symbol)} / {formatMoney(item.allocated, symbol)}
              </span>
            </div>
            <BudgetProgress percent={item.used_percent} color={item.category_color} />
            <p className="mt-2 text-xs text-ink-muted">{item.insight}</p>
          </div>
        ))}
      </div>
      <BottomSheet open={open} onClose={() => setOpen(false)} title="Budget category">
        <div className="space-y-3">
          <Field label="Category">
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Choose</option>
              {(categories || []).map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Monthly amount">
            <AmountInput value={amount} onChange={setAmount} symbol={symbol} />
          </Field>
          <Button className="w-full" disabled={!category || !amount || save.isPending} onClick={() => save.mutate()}>
            Save
          </Button>
        </div>
      </BottomSheet>
    </div>
  );
}
