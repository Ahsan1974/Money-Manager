import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { useState } from "react";
import { api } from "@/api/client";
import { unwrap } from "@/utils/unwrap";
import { formatMoney } from "@/utils/money";
import { TransactionItem } from "@/components/money/TransactionItem";
import { StatCard } from "@/components/money/MoneyCard";
import { Button, Field, Input, Select } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import type { Account, Transaction } from "@/types";
import { useAuth } from "@/stores/auth";

export function AccountDetailPage() {
  const { id } = useParams();
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const { data: account } = useQuery({ queryKey: ["account", id], queryFn: () => api<Account>(`/api/accounts/${id}/`) });
  const { data: stats } = useQuery({
    queryKey: ["account-stats", id],
    queryFn: () => api<{ income: string; expenses: string; current_balance: string; trend: { label: string; income: string; expenses: string }[] }>(`/api/accounts/${id}/stats/?year=${new Date().getFullYear()}&month=${new Date().getMonth() + 1}`),
  });
  const { data: txPage } = useQuery({
    queryKey: ["account-tx", id],
    queryFn: () => api<{ results: Transaction[] }>(`/api/transactions/?account=${id}`),
  });
  const { data: accounts } = useQuery({ queryKey: ["accounts"], queryFn: () => api<Account[] | { results: Account[] }>("/api/accounts/") });
  const others = unwrap(accounts).filter((item) => String(item.id) !== id);
  const [open, setOpen] = useState(false);
  const [amount, setAmount] = useState("");
  const [to, setTo] = useState("");
  const qc = useQueryClient();
  const transfer = useMutation({
    mutationFn: () =>
      api("/api/transfers/", {
        method: "POST",
        body: JSON.stringify({
          from_account: Number(id),
          to_account: Number(to),
          amount,
          transfer_date: new Date().toISOString().slice(0, 10),
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries();
      setOpen(false);
    },
  });

  if (!account) return <p className="text-sm text-ink-muted">Loading…</p>;

  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">{account.institution || account.account_type}</p>
        <h1 className="font-display text-3xl">{account.name}</h1>
        <p className="tabular mt-2 text-4xl font-semibold">{formatMoney(account.current_balance, symbol)}</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Income" value={formatMoney(stats?.income || 0, symbol)} tone="good" />
        <StatCard label="Expenses" value={formatMoney(stats?.expenses || 0, symbol)} />
      </div>
      <Button variant="ghost" className="w-full" onClick={() => setOpen(true)}>
        Transfer from this account
      </Button>
      <section>
        <h2 className="mb-2 font-medium">History</h2>
        {txPage?.results.map((tx) => (
          <TransactionItem key={tx.id} tx={tx} symbol={symbol} />
        ))}
      </section>
      <BottomSheet open={open} onClose={() => setOpen(false)} title="Transfer">
        <div className="space-y-3">
          <Field label="To">
            <Select value={to} onChange={(e) => setTo(e.target.value)}>
              <option value="">Choose account</option>
              {others.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Amount">
            <Input inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </Field>
          <Button className="w-full" disabled={!to || !amount || transfer.isPending} onClick={() => transfer.mutate()}>
            Move money
          </Button>
          <p className="text-xs text-ink-muted">Transfers are not counted as expenses.</p>
        </div>
      </BottomSheet>
    </div>
  );
}
