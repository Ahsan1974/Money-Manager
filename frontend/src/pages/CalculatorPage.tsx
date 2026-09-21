import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/api/client";
import { Button, Field, Input, Select } from "@/components/ui/primitives";
import { formatMoney } from "@/utils/money";
import { useAuth } from "@/stores/auth";

export function CalculatorPage() {
  const symbol = useAuth((s) => s.profile?.currency_symbol) || "Rs.";
  const [kind, setKind] = useState("savings");
  const [payload, setPayload] = useState<Record<string, string>>({ monthly_contribution: "20000", months: "24", annual_rate_pct: "0" });
  const [result, setResult] = useState<Record<string, string> | null>(null);
  const run = useMutation({
    mutationFn: () => api<Record<string, string>>("/api/calculator/", { method: "POST", body: JSON.stringify({ kind, payload }) }),
    onSuccess: setResult,
  });
  return (
    <div className="space-y-4">
      <h1 className="font-display text-3xl">Calculators</h1>
      <Field label="Type">
        <Select
          value={kind}
          onChange={(e) => {
            setKind(e.target.value);
            setResult(null);
          }}
        >
          <option value="savings">Savings</option>
          <option value="loan">Loan payment</option>
          <option value="debt_payoff">Debt payoff</option>
          <option value="percent">Percentage</option>
          <option value="fx">Currency conversion</option>
        </Select>
      </Field>
      {kind === "savings" && (
        <>
          <Field label="Monthly contribution">
            <Input value={payload.monthly_contribution || ""} onChange={(e) => setPayload({ ...payload, monthly_contribution: e.target.value })} />
          </Field>
          <Field label="Months">
            <Input value={payload.months || ""} onChange={(e) => setPayload({ ...payload, months: e.target.value })} />
          </Field>
        </>
      )}
      {kind === "loan" && (
        <>
          <Field label="Principal">
            <Input value={payload.principal || ""} onChange={(e) => setPayload({ ...payload, principal: e.target.value })} />
          </Field>
          <Field label="Annual rate %">
            <Input value={payload.annual_rate_pct || ""} onChange={(e) => setPayload({ ...payload, annual_rate_pct: e.target.value })} />
          </Field>
          <Field label="Months">
            <Input value={payload.months || ""} onChange={(e) => setPayload({ ...payload, months: e.target.value })} />
          </Field>
        </>
      )}
      {kind === "debt_payoff" && (
        <>
          <Field label="Balance">
            <Input value={payload.balance || ""} onChange={(e) => setPayload({ ...payload, balance: e.target.value })} />
          </Field>
          <Field label="Monthly payment">
            <Input value={payload.monthly_payment || ""} onChange={(e) => setPayload({ ...payload, monthly_payment: e.target.value })} />
          </Field>
          <Field label="Annual rate %">
            <Input value={payload.annual_rate_pct || "0"} onChange={(e) => setPayload({ ...payload, annual_rate_pct: e.target.value })} />
          </Field>
        </>
      )}
      {kind === "percent" && (
        <>
          <Field label="Part">
            <Input value={payload.part || ""} onChange={(e) => setPayload({ ...payload, part: e.target.value })} />
          </Field>
          <Field label="Whole">
            <Input value={payload.whole || ""} onChange={(e) => setPayload({ ...payload, whole: e.target.value })} />
          </Field>
        </>
      )}
      {kind === "fx" && (
        <>
          <Field label="Amount">
            <Input value={payload.amount || ""} onChange={(e) => setPayload({ ...payload, amount: e.target.value })} />
          </Field>
          <Field label="Rate">
            <Input value={payload.rate || "1"} onChange={(e) => setPayload({ ...payload, rate: e.target.value })} />
          </Field>
        </>
      )}
      <Button className="w-full" onClick={() => run.mutate()} disabled={run.isPending}>
        Calculate
      </Button>
      {result && (
        <div className="rounded-card border border-paper-line p-4 text-sm dark:border-[#2a2c2a]">
          {Object.entries(result).map(([k, v]) => (
            <div key={k} className="flex justify-between py-1">
              <span className="capitalize text-ink-muted">{k.replaceAll("_", " ")}</span>
              <span className="tabular">{String(v).match(/^\d/) ? formatMoney(v, symbol) : String(v)}</span>
            </div>
          ))}
        </div>
      )}
      <p className="text-xs text-ink-muted">Currency conversion uses a rate you type. Live FX is not enabled.</p>
    </div>
  );
}
