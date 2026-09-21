export function money(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return 0;
  const asNumber = typeof value === "number" ? value : Number(String(value).replace(/,/g, ""));
  return Number.isFinite(asNumber) ? asNumber : 0;
}

export function formatMoney(
  value: string | number | null | undefined,
  symbol = "Rs.",
  hidden = false,
) {
  if (hidden) return `${symbol} •••••`;
  const amount = money(value);
  const formatted = new Intl.NumberFormat("en-PK", {
    maximumFractionDigits: 0,
    minimumFractionDigits: 0,
  }).format(Math.round(amount));
  const sign = amount < 0 ? "-" : "";
  return `${sign}${symbol} ${formatted.replace("-", "")}`;
}

export function formatCompact(value: string | number, symbol = "Rs.") {
  const amount = money(value);
  return `${symbol} ${new Intl.NumberFormat("en-PK", { maximumFractionDigits: 0 }).format(Math.round(amount))}`;
}

export function monthLabel(year: number, month: number) {
  return new Date(year, month - 1, 1).toLocaleDateString("en-GB", {
    month: "long",
    year: "numeric",
  });
}
