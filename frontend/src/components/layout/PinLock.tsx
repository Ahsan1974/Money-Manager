import { useEffect, useRef, useState } from "react";
import { api } from "@/api/client";
import { Button, Input } from "@/components/ui/primitives";
import { useAuth } from "@/stores/auth";
import { useUI } from "@/stores/ui";

export function PinLock() {
  const profile = useAuth((s) => s.profile);
  const locked = useUI((s) => s.locked);
  const setLocked = useUI((s) => s.setLocked);
  const logout = useAuth((s) => s.logout);
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const timer = useRef<number | null>(null);

  useEffect(() => {
    if (!profile?.pin_enabled) return;
    const minutes = profile.lock_after_minutes || 2;
    const bump = () => {
      if (timer.current) window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => setLocked(true), minutes * 60 * 1000);
    };
    ["pointerdown", "keydown"].forEach((evt) => window.addEventListener(evt, bump));
    bump();
    return () => {
      ["pointerdown", "keydown"].forEach((evt) => window.removeEventListener(evt, bump));
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [profile, setLocked]);

  if (!locked || !profile?.pin_enabled) return null;

  const submit = async () => {
    try {
      await api("/api/auth/pin/verify/", { method: "POST", body: JSON.stringify({ pin }) });
      setPin("");
      setError("");
      setLocked(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Incorrect PIN.");
      setPin("");
    }
  };

  return (
    <div className="fixed inset-0 z-[80] flex flex-col items-center justify-center bg-[var(--bg)] px-6">
      <p className="font-display text-4xl">MONEA</p>
      <p className="mt-2 text-sm text-ink-muted">Enter your PIN to continue</p>
      <Input
        className="mt-8 max-w-xs text-center text-2xl tracking-[0.6em]"
        inputMode="numeric"
        maxLength={4}
        value={pin}
        onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 4))}
        onKeyDown={(e) => e.key === "Enter" && pin.length === 4 && submit()}
        aria-label="PIN"
      />
      {error && <p className="mt-3 text-sm text-rose">{error}</p>}
      <Button className="mt-6 w-40" disabled={pin.length !== 4} onClick={submit}>
        Unlock
      </Button>
      <button className="mt-6 text-sm text-ink-muted" onClick={() => logout()}>
        Log out
      </button>
    </div>
  );
}
