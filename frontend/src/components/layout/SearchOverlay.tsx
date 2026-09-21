import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { api } from "@/api/client";
import { BottomSheet } from "@/components/ui/overlays";
import { Input } from "@/components/ui/primitives";
import { useUI } from "@/stores/ui";

type SearchResult = {
  transactions: { id: number; merchant: string; amount: string; date: string; type: string }[];
  accounts: { id: number; name: string }[];
  bills: { id: number; name: string }[];
  subscriptions: { id: number; name: string }[];
  goals: { id: number; name: string }[];
  categories: { id: number; name: string }[];
};

export function SearchOverlay() {
  const open = useUI((s) => s.searchOpen);
  const setOpen = useUI((s) => s.setSearchOpen);
  const [q, setQ] = useState("");
  const navigate = useNavigate();
  const { data } = useQuery({
    queryKey: ["search", q],
    queryFn: () => api<SearchResult>(`/api/search/?q=${encodeURIComponent(q)}`),
    enabled: open && q.length > 0,
  });

  const go = (path: string) => {
    setOpen(false);
    navigate(path);
  };

  return (
    <BottomSheet open={open} onClose={() => setOpen(false)} title="Search">
      <Input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Transactions, accounts, bills…" />
      <div className="mt-4 space-y-4 text-sm">
        {data?.transactions.map((row) => (
          <button key={`t${row.id}`} className="block w-full text-left" onClick={() => go("/app/transactions")}>
            {row.merchant}
          </button>
        ))}
        {data?.accounts.map((row) => (
          <button key={`a${row.id}`} className="block w-full text-left" onClick={() => go(`/app/accounts/${row.id}`)}>
            Account · {row.name}
          </button>
        ))}
        {data?.bills.map((row) => (
          <button key={`b${row.id}`} className="block w-full text-left" onClick={() => go("/app/bills")}>
            Bill · {row.name}
          </button>
        ))}
        {data?.goals.map((row) => (
          <button key={`g${row.id}`} className="block w-full text-left" onClick={() => go("/app/goals")}>
            Goal · {row.name}
          </button>
        ))}
        {!q && <p className="text-ink-muted">Type to search your workspace. Shortcut: /</p>}
      </div>
    </BottomSheet>
  );
}
