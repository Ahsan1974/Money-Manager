import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { unwrap } from "@/utils/unwrap";
import { formatMoney } from "@/utils/money";
import { EmptyState } from "@/components/ui/states";
import { AmountInput, Button, Field, Input } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import { BudgetProgress } from "@/components/money/Progress";
import { useAuth } from "@/stores/auth";

type Debt = {
  id: number;
  name: string;
  remaining_amount: string;
  original_amount: string;
  monthly_payment: string;
  debt_type: string;
};

export function DebtsPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data } = useQuery({ queryKey: ["debts"], queryFn: () => api<Debt[] | { results: Debt[] }>("/api/debts/") });
  const debts = unwrap(data);
  const [open, setOpen] = useState(false);
  const [pay, setPay] = useState<Debt | null>(null);
  const [form, setForm] = useState({ name: "", original_amount: "", remaining_amount: "", monthly_payment: "", debt_type: "loan" });
  const [amount, setAmount] = useState("");
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: () => api("/api/debts/", { method: "POST", body: JSON.stringify({ ...form, remaining_amount: form.remaining_amount || form.original_amount }) }),
    onSuccess: () => {
      qc.invalidateQueries();
      setOpen(false);
    },
  });
  const repay = useMutation({
    mutationFn: () => api(`/api/debts/${pay!.id}/pay/`, { method: "POST", body: JSON.stringify({ amount, paid_on: new Date().toISOString().slice(0, 10) }) }),
    onSuccess: () => {
      qc.invalidateQueries();
      setPay(null);
    },
  });

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Liabilities</p>
          <h1 className="font-display text-3xl">Debts</h1>
        </div>
        <Button onClick={() => setOpen(true)}>Add</Button>
      </div>
      {!debts.length && <EmptyState title="No debts tracked" body="Add loans, installments, or card balances you want to pay down." action="Add debt" onAction={() => setOpen(true)} />}
      <div className="space-y-3">
        {debts.map((debt) => {
          const pct = (Number(debt.remaining_amount) / Math.max(Number(debt.original_amount), 1)) * 100;
          return (
            <div key={debt.id} className="rounded-card border border-paper-line p-4 dark:border-[#2a2c2a]">
              <div className="flex justify-between">
                <p className="font-medium">{debt.name}</p>
                <p className="tabular">{formatMoney(debt.remaining_amount, symbol)}</p>
              </div>
              <p className="mb-2 text-xs text-ink-muted">
                of {formatMoney(debt.original_amount, symbol)} · {formatMoney(debt.monthly_payment, symbol)} / month
              </p>
              <BudgetProgress percent={pct} color="#9F2D3A" />
              <Button variant="soft" className="mt-3 min-h-9 text-xs" onClick={() => setPay(debt)}>
                Record payment
              </Button>
            </div>
          );
        })}
      </div>
      <BottomSheet open={open} onClose={() => setOpen(false)} title="New debt">
        <div className="space-y-3">
          <Field label="Name">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Original amount">
            <AmountInput value={form.original_amount} onChange={(v) => setForm({ ...form, original_amount: v })} symbol={symbol} />
          </Field>
          <Field label="Remaining">
            <AmountInput value={form.remaining_amount} onChange={(v) => setForm({ ...form, remaining_amount: v })} symbol={symbol} />
          </Field>
          <Field label="Monthly payment">
            <AmountInput value={form.monthly_payment} onChange={(v) => setForm({ ...form, monthly_payment: v })} symbol={symbol} />
          </Field>
          <Button className="w-full" disabled={!form.name || !form.original_amount || save.isPending} onClick={() => save.mutate()}>
            Save
          </Button>
        </div>
      </BottomSheet>
      <BottomSheet open={!!pay} onClose={() => setPay(null)} title="Record payment">
        <AmountInput value={amount} onChange={setAmount} symbol={symbol} />
        <Button className="mt-4 w-full" disabled={!amount || repay.isPending} onClick={() => repay.mutate()}>
          Save payment
        </Button>
      </BottomSheet>
    </div>
  );
}
