import { forwardRef, type ButtonHTMLAttributes, type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

export function Button({
  className,
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "danger" | "soft" }) {
  const styles = {
    primary: "bg-ink text-paper-raised dark:bg-forest-dark dark:text-ink",
    ghost: "bg-transparent text-ink border border-paper-line dark:border-[#2a2c2a] dark:text-[#efece6]",
    danger: "bg-rose text-white",
    soft: "bg-forest-soft text-forest dark:bg-[#1a2a22] dark:text-forest-dark",
  };
  return (
    <button
      className={cn(
        "inline-flex min-h-11 items-center justify-center rounded-full px-5 text-sm font-medium transition active:scale-[0.98] disabled:opacity-50",
        styles[variant],
        className,
      )}
      {...props}
    />
  );
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input(
  { className, ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      className={cn(
        "min-h-12 w-full rounded-2xl border border-paper-line bg-paper-raised px-4 text-base text-ink outline-none dark:border-[#2a2c2a] dark:bg-[#161816] dark:text-[#efece6]",
        className,
      )}
      {...props}
    />
  );
});

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "min-h-12 w-full rounded-2xl border border-paper-line bg-paper-raised px-4 text-base text-ink outline-none dark:border-[#2a2c2a] dark:bg-[#161816] dark:text-[#efece6]",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-24 w-full rounded-2xl border border-paper-line bg-paper-raised px-4 py-3 text-base text-ink outline-none dark:border-[#2a2c2a] dark:bg-[#161816] dark:text-[#efece6]",
        className,
      )}
      {...props}
    />
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs font-medium uppercase tracking-[0.14em] text-ink-muted">{label}</span>
      {children}
    </label>
  );
}

export function AmountInput({
  value,
  onChange,
  symbol = "Rs.",
}: {
  value: string;
  onChange: (value: string) => void;
  symbol?: string;
}) {
  return (
    <div className="flex items-baseline gap-2 rounded-2xl border border-paper-line bg-paper-raised px-4 py-3 dark:border-[#2a2c2a] dark:bg-[#161816]">
      <span className="text-lg text-ink-muted">{symbol}</span>
      <input
        inputMode="decimal"
        value={value}
        onChange={(e) => onChange(e.target.value.replace(/[^\d.]/g, ""))}
        placeholder="0"
        aria-label="Amount"
        className="tabular w-full bg-transparent text-4xl font-semibold tracking-tight outline-none"
      />
    </div>
  );
}
