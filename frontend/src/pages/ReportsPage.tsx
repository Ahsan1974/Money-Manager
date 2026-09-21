import { api, apiBlob } from "@/api/client";
import { Button } from "@/components/ui/primitives";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

async function download(path: string, filename: string) {
  const blob = await apiBlob(path);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ReportsPage() {
  const now = new Date();
  const [busy, setBusy] = useState("");
  const navigate = useNavigate();
  const run = async (label: string, fn: () => Promise<void>) => {
    setBusy(label);
    try {
      await fn();
    } finally {
      setBusy("");
    }
  };
  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs uppercase tracking-[0.16em] text-ink-muted">Exports</p>
        <h1 className="font-display text-3xl">Reports</h1>
      </div>
      <p className="text-sm text-ink-muted">Professional snapshots of your own books. Not financial advice.</p>
      <div className="space-y-3">
        <Button
          className="w-full"
          disabled={!!busy}
          onClick={() =>
            run("pdf", () => download(`/api/reports/pdf/?year=${now.getFullYear()}&month=${now.getMonth() + 1}`, "monea-month.pdf"))
          }
        >
          {busy === "pdf" ? "Preparing…" : "This month PDF"}
        </Button>
        <Button
          variant="ghost"
          className="w-full"
          disabled={!!busy}
          onClick={() => run("year", () => download(`/api/reports/pdf/?year=${now.getFullYear()}`, "monea-year.pdf"))}
        >
          Yearly PDF
        </Button>
        <Button variant="ghost" className="w-full" disabled={!!busy} onClick={() => run("csv", () => download("/api/export/?format=csv", "monea.csv"))}>
          Transactions CSV
        </Button>
        <Button variant="ghost" className="w-full" disabled={!!busy} onClick={() => run("xlsx", () => download("/api/export/?format=xlsx", "monea.xlsx"))}>
          Transactions Excel
        </Button>
        <Button variant="ghost" className="w-full" onClick={() => navigate("/app/import")}>
          Import CSV / Excel
        </Button>
        <Button variant="ghost" className="w-full" disabled={!!busy} onClick={() => run("backup", () => download("/api/backup/", "monea-backup.json"))}>
          JSON backup
        </Button>
      </div>
    </div>
  );
}
