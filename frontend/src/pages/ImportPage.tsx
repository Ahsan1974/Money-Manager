import { useMutation, useState } from "react";
import { api } from "@/api/client";
import { unwrap } from "@/utils/unwrap";
import { useQuery } from "@tanstack/react-query";
import { Button, Field, Select } from "@/components/ui/primitives";
import type { Account } from "@/types";
import { useUI } from "@/stores/ui";

type Session = { id: number; columns: string[]; mapping: Record<string, string>; preview: Record<string, unknown>[] };

export function ImportPage() {
  const toast = useUI((s) => s.toast);
  const { data: accounts } = useQuery({ queryKey: ["accounts"], queryFn: () => api<Account[] | { results: Account[] }>("/api/accounts/") });
  const list = unwrap(accounts);
  const [account, setAccount] = useState("");
  const [session, setSession] = useState<Session | null>(null);
  const [preview, setPreview] = useState<{ date: string; amount: string; merchant: string; duplicate: boolean; type: string }[] | null>(null);

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData();
      body.append("file", file);
      return api<Session>("/api/import/upload/", { method: "POST", body });
    },
    onSuccess: setSession,
    onError: (e: Error) => toast(e.message, "error"),
  });

  const doPreview = useMutation({
    mutationFn: () =>
      api<{ preview: typeof preview }>(`/api/import/${session!.id}/preview/`, {
        method: "POST",
        body: JSON.stringify({ account: Number(account), mapping: session!.mapping }),
      }),
    onSuccess: (d) => setPreview(d.preview || []),
  });

  const commit = useMutation({
    mutationFn: () =>
      api<{ created: number; skipped: number }>(`/api/import/${session!.id}/commit/`, {
        method: "POST",
        body: JSON.stringify({ account: Number(account), skip_duplicates: true }),
      }),
    onSuccess: (d) => toast(`Imported ${d.created} rows, skipped ${d.skipped}.`),
  });

  return (
    <div className="space-y-5">
      <h1 className="font-display text-3xl">Import</h1>
      <p className="text-sm text-ink-muted">Upload a statement, map columns, review duplicates, then confirm.</p>
      <Field label="Account">
        <Select value={account} onChange={(e) => setAccount(e.target.value)}>
          <option value="">Choose</option>
          {list.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </Select>
      </Field>
      <input
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={(e) => e.target.files?.[0] && upload.mutate(e.target.files[0])}
      />
      {session && (
        <>
          <p className="text-sm text-ink-muted">Detected columns: {session.columns.join(", ") || "none"}</p>
          <Button disabled={!account || doPreview.isPending} onClick={() => doPreview.mutate()}>
            Preview
          </Button>
        </>
      )}
      {preview && (
        <div className="space-y-2">
          {preview.slice(0, 20).map((row, i) => (
            <div key={i} className="flex justify-between text-sm">
              <span>
                {row.date} · {row.merchant} {row.duplicate ? "(duplicate)" : ""}
              </span>
              <span className="tabular">{row.amount}</span>
            </div>
          ))}
          <Button className="w-full" onClick={() => commit.mutate()} disabled={commit.isPending}>
            Confirm import
          </Button>
        </div>
      )}
    </div>
  );
}
