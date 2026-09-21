import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { unwrap } from "@/utils/unwrap";
import { EmptyState } from "@/components/ui/states";
import { Button } from "@/components/ui/primitives";
import { format } from "date-fns";

type Note = { id: number; title: string; message: string; created_at: string; is_read: boolean; kind: string };

export function NotificationsPage() {
  const { data } = useQuery({ queryKey: ["notifications"], queryFn: () => api<Note[] | { results: Note[] }>("/api/notifications/") });
  const notes = unwrap(data);
  const qc = useQueryClient();
  const readAll = useMutation({
    mutationFn: () => api("/api/notifications/read_all/", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <h1 className="font-display text-3xl">Notifications</h1>
        <Button variant="ghost" onClick={() => readAll.mutate()}>
          Mark all read
        </Button>
      </div>
      {!notes.length && <EmptyState title="You're up to date" body="Bill reminders, budget alerts and renewals will appear here." />}
      <div className="space-y-3">
        {notes.map((note) => (
          <div key={note.id} className={`rounded-card border p-4 ${note.is_read ? "border-paper-line dark:border-[#2a2c2a]" : "border-forest"}`}>
            <p className="font-medium">{note.title}</p>
            <p className="mt-1 text-sm text-ink-muted">{note.message}</p>
            <p className="mt-2 text-xs text-ink-muted">{format(new Date(note.created_at), "d MMM · HH:mm")}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
