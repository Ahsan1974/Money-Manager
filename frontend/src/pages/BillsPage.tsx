import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useState } from "react";
import { api } from "@/api/client";
import { unwrap } from "@/utils/unwrap";
import { formatMoney } from "@/utils/money";
import { EmptyState } from "@/components/ui/states";
import { AmountInput, Button, Field, Input, Select } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import { useAuth } from "@/stores/auth";

type Bill = {
  id: number;
  name: string;
  amount: string;
  due_date: string;
  frequency: string;
  status: string;
};

export function BillsPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data } = useQuery({ queryKey: ["bills"], queryFn: () => api<Bill[] | { results: Bill[] }>("/api/bills/") });
  const { data: calendar } = useQuery({ queryKey: ["bill-calendar"], queryFn: () => api<Bill[]>("/api/bills/calendar/") });
  const bills = unwrap(data);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", amount: "", due_date: "", frequency: "monthly" });
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: () => api("/api/bills/", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => {
      qc.invalidateQueries();
      setOpen(false);
    },
  });
  const pay = useMutation({
    mutationFn: (id: number) => api(`/api/bills/${id}/pay/`, { method: "POST", body: JSON.stringify({ create_transaction: true }) }),
    onSuccess: () => qc.invalidateQueries(),
  });

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Obligations</p>
          <h1 className="font-display text-3xl">Bills</h1>
        </div>
        <Button onClick={() => setOpen(true)}>Add</Button>
      </div>
      {!bills.length && <EmptyState title="No bills yet" body="Track rent, utilities and anything that repeats." action="Add bill" onAction={() => setOpen(true)} />}
      <div className="space-y-3">
        {bills.map((bill) => (
          <div key={bill.id} className="rounded-card border border-paper-line p-4 dark:border-[#2a2c2a]">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium">{bill.name}</p>
                <p className="text-xs capitalize text-ink-muted">
                  {format(new Date(bill.due_date), "d MMM")} · {bill.status.replace("_", " ")} · {bill.frequency}
                </p>
              </div>
              <p className="tabular font-semibold">{formatMoney(bill.amount, symbol)}</p>
            </div>
            {bill.status !== "paid" && (
              <Button variant="soft" className="mt-3 min-h-9 text-xs" onClick={() => pay.mutate(bill.id)}>
                Mark paid
              </Button>
            )}
          </div>
        ))}
      </div>
      {!!calendar?.length && (
        <section className="mt-8">
          <h2 className="mb-3 font-medium">Calendar</h2>
          <div className="space-y-2">
            {calendar.map((bill) => (
              <div key={bill.id} className="flex justify-between text-sm">
                <span>
                  {format(new Date(bill.due_date), "d MMM")} · {bill.name}
                </span>
                <span className="tabular">{formatMoney(bill.amount, symbol)}</span>
              </div>
            ))}
          </div>
        </section>
      )}
      <BottomSheet open={open} onClose={() => setOpen(false)} title="New bill">
        <div className="space-y-3">
          <Field label="Name">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Amount">
            <AmountInput value={form.amount} onChange={(v) => setForm({ ...form, amount: v })} symbol={symbol} />
          </Field>
          <Field label="Due date">
            <Input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
          </Field>
          <Field label="Frequency">
            <Select value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })}>
              <option value="once">Once</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </Select>
          </Field>
          <Button className="w-full" disabled={!form.name || !form.amount || !form.due_date || save.isPending} onClick={() => save.mutate()}>
            Save bill
          </Button>
        </div>
      </BottomSheet>
    </div>
  );
}
