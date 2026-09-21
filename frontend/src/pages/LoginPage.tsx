import { useEffect, useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { api } from "@/api/client";
import { Button, Field, Input } from "@/components/ui/primitives";
import { useAuth } from "@/stores/auth";

export function LoginPage() {
  const { profile, login, register } = useAuth();
  const [needsRegistration, setNeedsRegistration] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("Ahsan Nadeem");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<{ needs_registration: boolean }>("/api/auth/bootstrap/", { skipAuth: true }).then((data) =>
      setNeedsRegistration(data.needs_registration),
    );
  }, []);

  if (profile) return <Navigate to="/app" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (needsRegistration) await register(username, password, displayName || username);
      else await login(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-dvh flex-col justify-between bg-[var(--bg)] px-6 py-10">
      <div>
        <p className="font-display text-5xl">MONEA</p>
        <p className="mt-2 text-xs uppercase tracking-[0.24em] text-ink-muted">Personal Finance OS</p>
        <p className="mt-8 max-w-xs text-lg text-ink-muted">A private home for your money. Nothing leaves this device unless you export it.</p>
      </div>
      <form onSubmit={submit} className="space-y-4">
        {needsRegistration && (
          <Field label="Your name">
            <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} autoComplete="name" placeholder="Ahsan Nadeem" />
          </Field>
        )}
        <Field label="Username">
          <Input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
        </Field>
        <Field label="Password">
          <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={needsRegistration ? "new-password" : "current-password"} required />
        </Field>
        {error && <p className="text-sm text-rose">{error}</p>}
        <Button className="w-full" disabled={busy}>
          {needsRegistration ? "Create workspace" : "Enter"}
        </Button>
      </form>
    </div>
  );
}
