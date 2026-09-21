import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { api } from "@/api/client";
import { unwrap } from "@/utils/unwrap";
import { formatMoney } from "@/utils/money";
import { EmptyState } from "@/components/ui/states";
import { AmountInput, Button, Field, Input, Select, Textarea } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import { CategoryIcon } from "@/components/money/CategoryIcon";
import type { Account } from "@/types";
import { useAuth } from "@/stores/auth";

const TYPES = [
  ["bank", "Bank account"],
  ["cash", "Cash"],
  ["credit_card", "Credit card"],
  ["savings", "Savings"],
  ["wallet", "Digital wallet"],
  ["investment", "Investment"],
  ["other", "Other"],
];

export function AccountsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["accounts"], queryFn: () => api<Account[] | { results: Account[] }>("/api/accounts/") });
  const accounts = unwrap(data);
  const [open, setOpen] = useState(false);
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: "", institution: "", account_type: "bank", opening_balance: "", color: "#1F6B4A", notes: "" });
  const save = useMutation({
    mutationFn: () => api("/api/accounts/", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["accounts"] });
      setOpen(false);
    },
  });

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Where it lives</p>
          <h1 className="font-display text-3xl">Accounts</h1>
        </div>
        <Button onClick={() => setOpen(true)}>Add</Button>
      </div>
      {isLoading && <p className="text-sm text-ink-muted">Loading…</p>}
      {!accounts.length && !isLoading && (
        <EmptyState title="No accounts yet" body="Add the places your money actually lives." action="Add account" onAction={() => setOpen(true)} />
      )}
      <div className="space-y-3">
        {accounts.map((account) => (
          <button
            key={account.id}
            onClick={() => navigate(`/app/accounts/${account.id}`)}
            className="flex w-full items-center gap-3 rounded-card border border-paper-line bg-paper-raised p-4 text-left dark:border-[#2a2c2a] dark:bg-[#161816]"
          >
            <CategoryIcon name={account.icon} color={account.color} />
            <div className="flex-1">
              <p className="font-medium">{account.name}</p>
              <p className="text-xs text-ink-muted">{account.institution || account.account_type.replace("_", " ")}</p>
            </div>
            <p className="tabular font-semibold">{formatMoney(account.current_balance, symbol)}</p>
          </button>
        ))}
      </div>
      <BottomSheet open={open} onClose={() => setOpen(false)} title="New account">
        <div className="space-y-3">
          <Field label="Name">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Institution">
            <Input value={form.institution} onChange={(e) => setForm({ ...form, institution: e.target.value })} />
          </Field>
          <Field label="Type">
            <Select value={form.account_type} onChange={(e) => setForm({ ...form, account_type: e.target.value })}>
              {TYPES.map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Opening balance">
            <AmountInput value={form.opening_balance} onChange={(v) => setForm({ ...form, opening_balance: v })} symbol={symbol} />
          </Field>
          <Field label="Notes">
            <Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </Field>
          <Button className="w-full" disabled={!form.name || save.isPending} onClick={() => save.mutate()}>
            Save account
          </Button>
        </div>
      </BottomSheet>
    </div>
  );
}
