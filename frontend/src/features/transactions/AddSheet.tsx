import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, enqueueTransaction } from "@/api/client";
import { AmountInput, Button, Field, Input, Select, Textarea } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import type { Account, Category, Transaction } from "@/types";
import { useUI } from "@/stores/ui";

export function AddSheet({
  open,
  onClose,
  editing,
}: {
  open: boolean;
  onClose: () => void;
  editing?: Transaction | null;
}) {
  const toast = useUI((s) => s.toast);
  const qc = useQueryClient();
  const { data: accounts } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => api<Account[] | { results: Account[] }>("/api/accounts/"),
    enabled: open,
  });
  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api<Category[]>("/api/categories/"),
    enabled: open,
  });
  const accountList = Array.isArray(accounts) ? accounts : accounts?.results || [];
  const [amount, setAmount] = useState("");
  const [type, setType] = useState<"expense" | "income">("expense");
  const [account, setAccount] = useState("");
  const [category, setCategory] = useState("");
  const [merchant, setMerchant] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState("");
  const [method, setMethod] = useState("card");
  const [nl, setNl] = useState("");

  useEffect(() => {
    if (editing) {
      setAmount(String(editing.amount));
      setType(editing.transaction_type === "income" ? "income" : "expense");
      setAccount(String(editing.account));
      setCategory(editing.category ? String(editing.category) : "");
      setMerchant(editing.merchant || editing.description);
      setDate(editing.transaction_date);
      setNotes(editing.notes || "");
      setMethod(editing.payment_method || "card");
    } else if (open) {
      setAmount("");
      setMerchant("");
      setNotes("");
      setDate(new Date().toISOString().slice(0, 10));
      setType("expense");
      if (accountList[0]) setAccount(String(accountList[0].id));
    }
  }, [editing, open]);

  const save = useMutation({
    mutationFn: async () => {
      const payload = {
        amount,
        transaction_type: type,
        account: Number(account),
        category: category ? Number(category) : null,
        merchant,
        description: merchant,
        transaction_date: date,
        notes,
        payment_method: method,
      };
      if (!navigator.onLine) {
        enqueueTransaction(payload);
        return { queued: true };
      }
      if (editing) return api(`/api/transactions/${editing.id}/`, { method: "PATCH", body: JSON.stringify(payload) });
      return api("/api/transactions/", { method: "POST", body: JSON.stringify(payload) });
    },
    onSuccess: (data) => {
      qc.invalidateQueries();
      toast(data && typeof data === "object" && "queued" in data ? "Saved offline. Will sync when you are back online." : "Transaction saved.");
      onClose();
    },
    onError: (err: Error) => toast(err.message, "error"),
  });

  const parse = useMutation({
    mutationFn: () => api<{ ok: boolean; error?: string; draft?: Record<string, string> }>("/api/parse/", { method: "POST", body: JSON.stringify({ text: nl }) }),
    onSuccess: (data) => {
      if (!data.ok) {
        toast(data.error || "Could not parse that.", "error");
        return;
      }
      const draft = data.draft!;
      setAmount(draft.amount);
      setType(draft.transaction_type === "income" ? "income" : "expense");
      if (draft.account) setAccount(String(draft.account));
      if (draft.category) setCategory(String(draft.category));
      setMerchant(draft.merchant || draft.description);
      setDate(draft.transaction_date);
      toast("Review the details, then save.");
    },
  });

  const cats = (categories || []).flatMap((c) => [c, ...(c.children || [])]);

  return (
    <BottomSheet open={open} onClose={onClose} title={editing ? "Edit transaction" : "Add transaction"}>
      <div className="space-y-4">
        <Field label="Type it naturally">
          <div className="flex gap-2">
            <Input value={nl} onChange={(e) => setNl(e.target.value)} placeholder='e.g. "450 lunch"' />
            <Button variant="soft" type="button" onClick={() => parse.mutate()} disabled={!nl.trim()}>
              Parse
            </Button>
          </div>
        </Field>
        <AmountInput value={amount} onChange={setAmount} />
        <div className="grid grid-cols-2 gap-2">
          {(["expense", "income"] as const).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setType(item)}
              className={`min-h-11 rounded-full text-sm font-medium capitalize ${
                type === item ? "bg-ink text-paper-raised dark:bg-forest-dark" : "border border-paper-line dark:border-[#2a2c2a]"
              }`}
            >
              {item}
            </button>
          ))}
        </div>
        <Field label="Account">
          <Select value={account} onChange={(e) => setAccount(e.target.value)}>
            {accountList.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Category">
          <Select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">Uncategorized</option>
            {cats.map((item) => (
              <option key={item.id} value={item.id}>
                {item.parent ? "— " : ""}
                {item.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Merchant">
          <Input value={merchant} onChange={(e) => setMerchant(e.target.value)} placeholder="Where did this happen?" />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Date">
            <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </Field>
          <Field label="Method">
            <Select value={method} onChange={(e) => setMethod(e.target.value)}>
              <option value="card">Card</option>
              <option value="cash">Cash</option>
              <option value="bank">Bank</option>
              <option value="wallet">Wallet</option>
              <option value="other">Other</option>
            </Select>
          </Field>
        </div>
        <Field label="Notes">
          <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional" />
        </Field>
        <Button className="w-full" disabled={!amount || !account || save.isPending} onClick={() => save.mutate()}>
          {save.isPending ? "Saving…" : "Save"}
        </Button>
      </div>
    </BottomSheet>
  );
}
