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

type Person = { id: number; name: string };
type RecordRow = {
  id: number;
  person: number;
  person_name: string;
  direction: string;
  amount: string;
  remaining_amount: string;
  reason: string;
  status: string;
  expected_repayment: string | null;
};

export function LendingPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data } = useQuery({ queryKey: ["lending"], queryFn: () => api<RecordRow[] | { results: RecordRow[] }>("/api/lending/") });
  const { data: summary } = useQuery({ queryKey: ["lending-summary"], queryFn: () => api<{ owed_to_me: string; i_owe: string }>("/api/lending/summary/") });
  const { data: people } = useQuery({ queryKey: ["people"], queryFn: () => api<Person[] | { results: Person[] }>("/api/people/") });
  const rows = unwrap(data);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ person_name: "", direction: "lent", amount: "", reason: "", expected_repayment: "" });
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: async () => {
      let personId = unwrap(people).find((p) => p.name.toLowerCase() === form.person_name.toLowerCase())?.id;
      if (!personId) {
        const person = await api<Person>("/api/people/", { method: "POST", body: JSON.stringify({ name: form.person_name }) });
        personId = person.id;
      }
      return api("/api/lending/", {
        method: "POST",
        body: JSON.stringify({
          person: personId,
          direction: form.direction,
          amount: form.amount,
          remaining_amount: form.amount,
          record_date: new Date().toISOString().slice(0, 10),
          reason: form.reason,
          expected_repayment: form.expected_repayment || null,
        }),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries();
      setOpen(false);
    },
  });
  const repay = useMutation({
    mutationFn: (id: number) =>
      api(`/api/lending/${id}/repay/`, {
        method: "POST",
        body: JSON.stringify({ amount: promptAmount, paid_on: new Date().toISOString().slice(0, 10) }),
      }),
    onSuccess: () => qc.invalidateQueries(),
  });
  const [promptAmount, setPromptAmount] = useState("");
  const [repaying, setRepaying] = useState<RecordRow | null>(null);

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">People</p>
          <h1 className="font-display text-3xl">Lending</h1>
        </div>
        <Button onClick={() => setOpen(true)}>Add</Button>
      </div>
      <div className="mb-5 grid grid-cols-2 gap-3">
        <StatCard label="Owed to me" value={formatMoney(summary?.owed_to_me || 0, symbol)} tone="good" />
        <StatCard label="I owe" value={formatMoney(summary?.i_owe || 0, symbol)} />
      </div>
      {!rows.length && <EmptyState title="No lending records" body="Track money you lent or borrowed so it does not disappear from memory." action="Add record" onAction={() => setOpen(true)} />}
      <div className="space-y-3">
        {rows.map((row) => (
          <div key={row.id} className="rounded-card border border-paper-line p-4 dark:border-[#2a2c2a]">
            <p className="font-medium">{row.person_name}</p>
            <p className="text-xs capitalize text-ink-muted">
              {row.direction} · {row.status} · {row.reason}
            </p>
            <p className="tabular mt-2">{formatMoney(row.remaining_amount, symbol)} remaining</p>
            {row.status !== "settled" && (
              <Button variant="soft" className="mt-3 min-h-9 text-xs" onClick={() => setRepaying(row)}>
                Record repayment
              </Button>
            )}
          </div>
        ))}
      </div>
      <BottomSheet open={open} onClose={() => setOpen(false)} title="Lending record">
        <div className="space-y-3">
          <Field label="Person">
            <Input value={form.person_name} onChange={(e) => setForm({ ...form, person_name: e.target.value })} />
          </Field>
          <Field label="Direction">
            <Select value={form.direction} onChange={(e) => setForm({ ...form, direction: e.target.value })}>
              <option value="lent">I lent</option>
              <option value="borrowed">I borrowed</option>
            </Select>
          </Field>
          <Field label="Amount">
            <AmountInput value={form.amount} onChange={(v) => setForm({ ...form, amount: v })} symbol={symbol} />
          </Field>
          <Field label="Reason">
            <Input value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
          </Field>
          <Field label="Expected repayment">
            <Input type="date" value={form.expected_repayment} onChange={(e) => setForm({ ...form, expected_repayment: e.target.value })} />
          </Field>
          <Button className="w-full" disabled={!form.person_name || !form.amount || save.isPending} onClick={() => save.mutate()}>
            Save
          </Button>
        </div>
      </BottomSheet>
      <BottomSheet open={!!repaying} onClose={() => setRepaying(null)} title="Repayment">
        <AmountInput value={promptAmount} onChange={setPromptAmount} symbol={symbol} />
        <Button
          className="mt-4 w-full"
          disabled={!promptAmount || repay.isPending}
          onClick={() => repaying && repay.mutate(repaying.id)}
        >
          Save
        </Button>
      </BottomSheet>
    </div>
  );
}
