import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import type { Category } from "@/types";
import { CategoryIcon } from "@/components/money/CategoryIcon";
import { Button, Field, Input, Select } from "@/components/ui/primitives";
import { BottomSheet } from "@/components/ui/overlays";
import { EmptyState } from "@/components/ui/states";

export function CategoriesPage() {
  const { data } = useQuery({ queryKey: ["categories"], queryFn: () => api<Category[]>("/api/categories/") });
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", parent: "", kind: "expense", color: "#6B7280", icon: "circle" });
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: () =>
      api("/api/categories/", {
        method: "POST",
        body: JSON.stringify({ ...form, parent: form.parent ? Number(form.parent) : null }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["categories"] });
      setOpen(false);
    },
  });
  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <h1 className="font-display text-3xl">Categories</h1>
        <Button onClick={() => setOpen(true)}>Add</Button>
      </div>
      {!data?.length && <EmptyState title="No categories" body="Categories appear after your first login." />}
      <div className="space-y-4">
        {data?.map((cat) => (
          <div key={cat.id}>
            <div className="flex items-center gap-3">
              <CategoryIcon name={cat.icon} color={cat.color} />
              <span className="font-medium">{cat.name}</span>
            </div>
            <div className="ml-12 mt-1 space-y-1 text-sm text-ink-muted">
              {cat.children?.map((child) => (
                <p key={child.id}>{child.name}</p>
              ))}
            </div>
          </div>
        ))}
      </div>
      <BottomSheet open={open} onClose={() => setOpen(false)} title="Category">
        <div className="space-y-3">
          <Field label="Name">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Parent">
            <Select value={form.parent} onChange={(e) => setForm({ ...form, parent: e.target.value })}>
              <option value="">None</option>
              {data?.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Kind">
            <Select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
              <option value="expense">Expense</option>
              <option value="income">Income</option>
              <option value="both">Both</option>
            </Select>
          </Field>
          <Button className="w-full" disabled={!form.name || save.isPending} onClick={() => save.mutate()}>
            Save
          </Button>
        </div>
      </BottomSheet>
    </div>
  );
}
