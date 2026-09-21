import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { Button, Input } from "@/components/ui/primitives";
import { useAuth } from "@/stores/auth";

type Ask = {
  reply: string;
  draft?: Record<string, string>;
  needs_confirmation?: boolean;
  conversation_id: number;
};

export function AssistantPage() {
  const enabled = useAuth((s) => s.profile?.ai_enabled);
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [draft, setDraft] = useState<Record<string, string> | null>(null);
  const ask = useMutation({
    mutationFn: () => api<Ask>("/api/ai/ask/", { method: "POST", body: JSON.stringify({ message: text }) }),
    onSuccess: (data) => {
      setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: data.reply }]);
      setDraft(data.draft || null);
      setText("");
    },
  });
  const confirm = useMutation({
    mutationFn: () => api("/api/ai/confirm/", { method: "POST", body: JSON.stringify({ draft }) }),
    onSuccess: () => {
      setMessages((m) => [...m, { role: "assistant", content: "Saved. The transaction is now in your ledger." }]);
      setDraft(null);
    },
  });

  return (
    <div className="flex min-h-[70vh] flex-col">
      <h1 className="font-display text-3xl">Assistant</h1>
      <p className="mt-1 text-sm text-ink-muted">
        Answers are grounded in your books. Groq is used when configured; the local engine is the fallback. Numbers are never invented.
      </p>
      <div className="mt-4 flex-1 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm ${msg.role === "user" ? "ml-auto bg-ink text-paper-raised" : "bg-paper-raised dark:bg-[#161816]"}`}>
            <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
          </div>
        ))}
        {draft && (
          <div className="rounded-2xl border border-paper-line p-4 text-sm dark:border-[#2a2c2a]">
            <p className="font-medium">Confirm this transaction</p>
            <p className="mt-2 text-ink-muted">
              {draft.amount} · {draft.description} · {draft.account_name}
            </p>
            <div className="mt-3 flex gap-2">
              <Button onClick={() => confirm.mutate()}>Confirm</Button>
              <Button variant="ghost" onClick={() => setDraft(null)}>
                Discard
              </Button>
            </div>
          </div>
        )}
      </div>
      <form
        className="mt-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (text.trim()) ask.mutate();
        }}
      >
        <Input value={text} onChange={(e) => setText(e.target.value)} placeholder="How much did I spend on food this month?" />
        <Button disabled={!text.trim() || ask.isPending || enabled === false}>Ask</Button>
      </form>
    </div>
  );
}
