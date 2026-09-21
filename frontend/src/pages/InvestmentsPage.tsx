import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { unwrap } from "@/utils/unwrap";
import { formatMoney } from "@/utils/money";
import { EmptyState } from "@/components/ui/states";
import { AmountInput, Button, Field, Input, Select } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import { useAuth } from "@/stores/auth";

type Inv = { id: number; name: string; investment_type: string; amount_invested: string; current_value: string; gain: string; purchased_on: string };

export function InvestmentsPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data } = useQuery({ queryKey: ["investments"], queryFn: () => api<Inv[] | { results: Inv[] }>("/api/investments/") });
  const rows = unwrap(data);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", investment_type: "other", amount_invested: "", current_value: "", purchased_on: "", notes: "" });
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: () => api("/api/investments/", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => {
      qc.invalidateQueries();
      setOpen(false);
    },
  });
  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Manual tracking</p>
          <h1 className="font-display text-3xl">Investments</h1>
        </div>
        <Button onClick={() => setOpen(true)}>Add</Button>
      </div>
      <p className="mb-4 text-sm text-ink-muted">This is a ledger, not a brokerage. No live prices, no trading.</p>
      {!rows.length && <EmptyState title="No investments" body="Record funds, gold, or certificates you already hold." action="Add" onAction={() => setOpen(true)} />}
      <div className="space-y-3">
        {rows.map((row) => (
          <div key={row.id} className="rounded-card border border-paper-line p-4 dark:border-[#2a2c2a]">
            <p className="font-medium">{row.name}</p>
            <p className="text-xs capitalize text-ink-muted">{row.investment_type}</p>
            <p className="tabular mt-2">{formatMoney(row.current_value, symbol)}</p>
            <p className="text-xs text-ink-muted">Invested {formatMoney(row.amount_invested, symbol)}</p>
          </div>
        ))}
      </div>
      <BottomSheet open={open} onClose={() => setOpen(false)} title="Investment">
        <div className="space-y-3">
          <Field label="Name">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Type">
            <Select value={form.investment_type} onChange={(e) => setForm({ ...form, investment_type: e.target.value })}>
              <option value="stock">Stock</option>
              <option value="fund">Fund</option>
              <option value="bond">Bond</option>
              <option value="gold">Gold</option>
              <option value="other">Other</option>
            </Select>
          </Field>
          <Field label="Amount invested">
            <AmountInput value={form.amount_invested} onChange={(v) => setForm({ ...form, amount_invested: v })} symbol={symbol} />
          </Field>
          <Field label="Current value">
            <AmountInput value={form.current_value} onChange={(v) => setForm({ ...form, current_value: v })} symbol={symbol} />
          </Field>
          <Field label="Date">
            <Input type="date" value={form.purchased_on} onChange={(e) => setForm({ ...form, purchased_on: e.target.value })} />
          </Field>
          <Button className="w-full" disabled={!form.name || !form.amount_invested || !form.current_value || !form.purchased_on || save.isPending} onClick={() => save.mutate()}>
            Save
          </Button>
        </div>
      </BottomSheet>
    </div>
  );
}
