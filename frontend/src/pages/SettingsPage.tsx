import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { Button, Field, Input, Select } from "@/components/ui/primitives";
import { ConfirmDialog } from "@/components/ui/overlays";
import type { Profile } from "@/types";
import { useAuth } from "@/stores/auth";
import { applyTheme, useUI } from "@/stores/ui";

export function SettingsPage() {
  const profile = useAuth((s) => s.profile);
  const setProfile = useAuth((s) => s.setProfile);
  const setTheme = useUI((s) => s.setTheme);
  const toast = useUI((s) => s.toast);
  const qc = useQueryClient();
  const [form, setForm] = useState<Partial<Profile>>(profile || {});
  const [pin, setPin] = useState("");
  const [restoreOpen, setRestoreOpen] = useState(false);
  const [restoreText, setRestoreText] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const save = useMutation({
    mutationFn: () => api<Profile>("/api/auth/me/", { method: "PATCH", body: JSON.stringify(form) }),
    onSuccess: (data) => {
      setProfile(data);
      setTheme(data.theme);
      applyTheme(data.theme);
      toast("Settings saved.");
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e: Error) => toast(e.message, "error"),
  });

  const setPinMut = useMutation({
    mutationFn: () => api("/api/auth/pin/set/", { method: "POST", body: JSON.stringify({ pin }) }),
    onSuccess: () => toast("PIN enabled."),
  });

  const restore = useMutation({
    mutationFn: async () => {
      const payload = file ? JSON.parse(await file.text()) : null;
      return api("/api/backup/restore/", { method: "POST", body: JSON.stringify({ confirmation: "RESTORE", payload }) });
    },
    onSuccess: () => {
      toast("Backup restored.");
      setRestoreOpen(false);
      qc.invalidateQueries();
    },
  });

  const patch = (key: keyof Profile, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  return (
    <div className="space-y-8 pb-8">
      <div>
        <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Workspace</p>
        <h1 className="font-display text-3xl">Settings</h1>
      </div>
      <section className="space-y-3">
        <h2 className="font-medium">Profile</h2>
        <Field label="Display name">
          <Input value={form.display_name || ""} onChange={(e) => patch("display_name", e.target.value)} />
        </Field>
        <Field label="Currency code">
          <Input value={form.currency || "PKR"} onChange={(e) => patch("currency", e.target.value)} />
        </Field>
        <Field label="Currency symbol">
          <Input value={form.currency_symbol || "Rs."} onChange={(e) => patch("currency_symbol", e.target.value)} />
        </Field>
      </section>
      <section className="space-y-3">
        <h2 className="font-medium">Appearance</h2>
        <Field label="Theme">
          <Select value={form.theme || "system"} onChange={(e) => patch("theme", e.target.value)}>
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </Select>
        </Field>
      </section>
      <section className="space-y-3">
        <h2 className="font-medium">Safe to spend</h2>
        <Field label="Emergency reserve">
          <Input value={String(form.emergency_reserve ?? "")} onChange={(e) => patch("emergency_reserve", e.target.value)} />
        </Field>
        <Field label="Savings reserve">
          <Input value={String(form.savings_reserve ?? "")} onChange={(e) => patch("savings_reserve", e.target.value)} />
        </Field>
        <Field label="Obligation horizon (days)">
          <Input type="number" value={form.obligation_horizon_days ?? 30} onChange={(e) => patch("obligation_horizon_days", Number(e.target.value))} />
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={!!form.include_upcoming_bills} onChange={(e) => patch("include_upcoming_bills", e.target.checked)} />
          Subtract upcoming bills
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={!!form.include_debt_payments} onChange={(e) => patch("include_debt_payments", e.target.checked)} />
          Subtract debt payments
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={!!form.include_goal_reserves} onChange={(e) => patch("include_goal_reserves", e.target.checked)} />
          Subtract reserved goals
        </label>
      </section>
      <section className="space-y-3">
        <h2 className="font-medium">Security</h2>
        <Field label="4-digit PIN">
          <Input inputMode="numeric" maxLength={4} value={pin} onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 4))} />
        </Field>
        <Button variant="ghost" disabled={pin.length !== 4} onClick={() => setPinMut.mutate()}>
          Enable PIN lock
        </Button>
      </section>
      <section className="space-y-3">
        <h2 className="font-medium">Notifications</h2>
        {[
          ["notify_bills", "Bills"],
          ["notify_budgets", "Budgets"],
          ["notify_subscriptions", "Subscriptions"],
          ["notify_goals", "Goals"],
          ["notify_unusual", "Unusual spending"],
        ].map(([key, label]) => (
          <label key={key} className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={!!form[key as keyof Profile]} onChange={(e) => patch(key as keyof Profile, e.target.checked)} />
            {label}
          </label>
        ))}
      </section>
      <Button className="w-full" onClick={() => save.mutate()} disabled={save.isPending}>
        Save settings
      </Button>
      <section className="space-y-3">
        <h2 className="font-medium">Backup</h2>
        <input type="file" accept="application/json" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <Button variant="ghost" className="w-full" onClick={() => setRestoreOpen(true)} disabled={!file}>
          Restore backup
        </Button>
      </section>
      <section>
        <h2 className="font-medium">About</h2>
        <p className="mt-2 text-sm text-ink-muted">MONEA is a private personal finance OS. It does not connect to banks or offer regulated advice.</p>
      </section>
      <ConfirmDialog
        open={restoreOpen}
        title="Restore backup?"
        body="This replaces your current data. Type RESTORE in the next step by confirming."
        confirmLabel="RESTORE"
        onClose={() => setRestoreOpen(false)}
        onConfirm={() => restore.mutate()}
      />
    </div>
  );
}
