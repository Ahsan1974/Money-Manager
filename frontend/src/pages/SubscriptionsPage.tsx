import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { unwrap } from "@/utils/unwrap";
import { formatMoney } from "@/utils/money";
import { EmptyState } from "@/components/ui/states";
import { AmountInput, Button, Field, Input, Select } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import { StatCard } from "@/components/money/MoneyCard";
import { useAuth } from "@/stores/auth";

type Sub = { id: number; name: string; price: string; billing_cycle: string; next_billing_date: string; monthly_cost: string; status: string };
type Summary = { monthly: string; annual: string; active: number; largest: string | null; insight: string };

export function SubscriptionsPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data } = useQuery({ queryKey: ["subs"], queryFn: () => api<Sub[] | { results: Sub[] }>("/api/subscriptions/") });
  const { data: summary } = useQuery({ queryKey: ["subs-summary"], queryFn: () => api<Summary>("/api/subscriptions/summary/") });
  const subs = unwrap(data);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", price: "", billing_cycle: "monthly", next_billing_date: "" });
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: () => api("/api/subscriptions/", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => {
      qc.invalidateQueries();
      setOpen(false);
    },
  });

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Recurring</p>
          <h1 className="font-display text-3xl">Subscriptions</h1>
        </div>
        <Button onClick={() => setOpen(true)}>Add</Button>
      </div>
      {summary && (
        <div className="mb-5 grid grid-cols-2 gap-3">
          <StatCard label="Monthly" value={formatMoney(summary.monthly, symbol)} />
          <StatCard label="Annual" value={formatMoney(summary.annual, symbol)} />
        </div>
      )}
      {summary?.insight && <p className="mb-4 text-sm text-ink-muted">{summary.insight}</p>}
      {!subs.length && <EmptyState title="No subscriptions" body="Track Netflix, tools, and anything that renews." action="Add subscription" onAction={() => setOpen(true)} />}
      <div className="space-y-3">
        {subs.map((sub) => (
          <div key={sub.id} className="flex items-center justify-between rounded-card border border-paper-line p-4 dark:border-[#2a2c2a]">
            <div>
              <p className="font-medium">{sub.name}</p>
              <p className="text-xs text-ink-muted">
                Next {sub.next_billing_date} · {sub.billing_cycle}
              </p>
            </div>
            <p className="tabular font-semibold">{formatMoney(sub.price, symbol)}</p>
          </div>
        ))}
      </div>
      <BottomSheet open={open} onClose={() => setOpen(false)} title="New subscription">
        <div className="space-y-3">
          <Field label="Name">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Price">
            <AmountInput value={form.price} onChange={(v) => setForm({ ...form, price: v })} symbol={symbol} />
          </Field>
          <Field label="Cycle">
            <Select value={form.billing_cycle} onChange={(e) => setForm({ ...form, billing_cycle: e.target.value })}>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </Select>
          </Field>
          <Field label="Next billing">
            <Input type="date" value={form.next_billing_date} onChange={(e) => setForm({ ...form, next_billing_date: e.target.value })} />
          </Field>
          <Button className="w-full" disabled={!form.name || !form.price || !form.next_billing_date || save.isPending} onClick={() => save.mutate()}>
            Save
          </Button>
        </div>
      </BottomSheet>
    </div>
  );
}
