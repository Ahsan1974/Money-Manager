import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "@/api/client";
import { TransactionItem } from "@/components/money/TransactionItem";
import { EmptyState } from "@/components/ui/states";
import { Button, Input, Select } from "@/components/ui/primitives";
import { ConfirmDialog } from "@/components/ui/overlays";
import { AddSheet } from "@/features/transactions/AddSheet";
import type { Transaction } from "@/types";
import { useUI } from "@/stores/ui";
import { useAuth } from "@/stores/auth";

type Page = { results: Transaction[]; next: string | null; count: number };

export function TransactionsPage() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState("");
  const [type, setType] = useState(params.get("type") || "");
  const category = params.get("category") || "";
  const [editing, setEditing] = useState<Transaction | null>(null);
  const [deleting, setDeleting] = useState<Transaction | null>(null);
  const setAddOpen = useUI((s) => s.setAddOpen);
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const qc = useQueryClient();

  const query = useMemo(() => {
    const sp = new URLSearchParams();
    if (q) sp.set("search", q);
    if (type) sp.set("transaction_type", type);
    if (category) sp.set("category", category);
    return `/api/transactions/?${sp.toString()}`;
  }, [q, type, category]);

  const { data, isLoading } = useQuery({
    queryKey: ["transactions", query],
    queryFn: () => api<Page>(query),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api(`/api/transactions/${id}/`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries();
      setDeleting(null);
    },
  });

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Activity</p>
          <h1 className="font-display text-3xl">Transactions</h1>
        </div>
        <Button onClick={() => setAddOpen(true)}>Add</Button>
      </div>
      <div className="mb-4 flex gap-2">
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search merchant or notes" />
        <Select value={type} onChange={(e) => setType(e.target.value)} className="max-w-32">
          <option value="">All</option>
          <option value="expense">Expense</option>
          <option value="income">Income</option>
          <option value="transfer">Transfer</option>
        </Select>
      </div>
      {isLoading && <p className="text-sm text-ink-muted">Loading…</p>}
      {!isLoading && !data?.results.length && (
        <EmptyState
          title="No transactions yet"
          body="Add your first transaction to start understanding your spending."
          action="Add transaction"
          onAction={() => setAddOpen(true)}
        />
      )}
      <div className="divide-y divide-paper-line dark:divide-[#2a2c2a]">
        {data?.results.map((tx) => (
          <div key={tx.id} className="flex items-center">
            <div className="flex-1">
              <TransactionItem tx={tx} symbol={symbol} onClick={() => setEditing(tx)} />
            </div>
            <button className="px-2 text-xs text-rose" onClick={() => setDeleting(tx)}>
              Delete
            </button>
          </div>
        ))}
      </div>
      <AddSheet open={!!editing} editing={editing} onClose={() => setEditing(null)} />
      <ConfirmDialog
        open={!!deleting}
        title="Delete transaction?"
        body="This updates your balances and analytics immediately."
        confirmLabel="Delete"
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && remove.mutate(deleting.id)}
      />
    </div>
  );
}
