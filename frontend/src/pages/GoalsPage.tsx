import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { unwrap } from "@/utils/unwrap";
import { formatMoney } from "@/utils/money";
import { GoalProgress } from "@/components/money/Progress";
import { EmptyState } from "@/components/ui/states";
import { AmountInput, Button, Field, Input } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import { useAuth } from "@/stores/auth";

type Goal = {
  id: number;
  name: string;
  target_amount: string;
  current_amount: string;
  target_date: string | null;
  color: string;
  remaining: string;
  progress: string;
  required_monthly: string;
  required_weekly: string;
};

export function GoalsPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data } = useQuery({ queryKey: ["goals"], queryFn: () => api<Goal[] | { results: Goal[] }>("/api/goals/") });
  const goals = unwrap(data);
  const [open, setOpen] = useState(false);
  const [contribute, setContribute] = useState<Goal | null>(null);
  const [form, setForm] = useState({ name: "", target_amount: "", target_date: "", current_amount: "0" });
  const [amount, setAmount] = useState("");
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: () => api("/api/goals/", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals"] });
      setOpen(false);
    },
  });
  const add = useMutation({
    mutationFn: () =>
      api(`/api/goals/${contribute!.id}/contribute/`, {
        method: "POST",
        body: JSON.stringify({ amount, contributed_on: new Date().toISOString().slice(0, 10) }),
      }),
    onSuccess: () => {
      qc.invalidateQueries();
      setContribute(null);
      setAmount("");
    },
  });

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">What you are saving for</p>
          <h1 className="font-display text-3xl">Goals</h1>
        </div>
        <Button onClick={() => setOpen(true)}>Add</Button>
      </div>
      {!goals.length && <EmptyState title="No goals yet" body="Name the thing you are saving toward and track the path to it." action="Add goal" onAction={() => setOpen(true)} />}
      <div className="space-y-3">
        {goals.map((goal) => (
          <div key={goal.id} className="flex gap-4 rounded-card border border-paper-line bg-paper-raised p-4 dark:border-[#2a2c2a] dark:bg-[#161816]">
            <GoalProgress percent={goal.progress} color={goal.color} />
            <div className="flex-1">
              <p className="font-medium">{goal.name}</p>
              <p className="tabular text-sm text-ink-muted">
                {formatMoney(goal.current_amount, symbol)} of {formatMoney(goal.target_amount, symbol)}
              </p>
              <p className="mt-1 text-xs text-ink-muted">
                {formatMoney(goal.required_monthly, symbol)} / month · {formatMoney(goal.required_weekly, symbol)} / week
              </p>
              <Button variant="soft" className="mt-3 min-h-9 px-4 text-xs" onClick={() => setContribute(goal)}>
                Contribute
              </Button>
            </div>
          </div>
        ))}
      </div>
      <BottomSheet open={open} onClose={() => setOpen(false)} title="New goal">
        <div className="space-y-3">
          <Field label="Name">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Target">
            <AmountInput value={form.target_amount} onChange={(v) => setForm({ ...form, target_amount: v })} symbol={symbol} />
          </Field>
          <Field label="Target date">
            <Input type="date" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })} />
          </Field>
          <Button className="w-full" disabled={!form.name || !form.target_amount || save.isPending} onClick={() => save.mutate()}>
            Save goal
          </Button>
        </div>
      </BottomSheet>
      <BottomSheet open={!!contribute} onClose={() => setContribute(null)} title={`Contribute to ${contribute?.name || ""}`}>
        <AmountInput value={amount} onChange={setAmount} symbol={symbol} />
        <Button className="mt-4 w-full" disabled={!amount || add.isPending} onClick={() => add.mutate()}>
          Add contribution
        </Button>
      </BottomSheet>
    </div>
  );
}
