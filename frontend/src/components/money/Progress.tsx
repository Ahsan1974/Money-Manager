export function BudgetProgress({
  percent,
  color,
}: {
  percent: string | number;
  color?: string;
}) {
  const value = Math.min(Math.max(Number(percent) || 0, 0), 140);
  const over = value >= 100;
  return (
    <div className="h-1.5 overflow-hidden rounded-full bg-paper-line dark:bg-[#2a2c2a]">
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${Math.min(value, 100)}%`, background: over ? "#9F2D3A" : color || "#1F6B4A" }}
      />
    </div>
  );
}

export function GoalProgress({ percent, color }: { percent: string | number; color?: string }) {
  const value = Math.min(Math.max(Number(percent) || 0, 0), 100);
  return (
    <div className="relative h-16 w-16">
      <svg viewBox="0 0 36 36" className="-rotate-90">
        <path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke="currentColor"
          className="text-paper-line dark:text-[#2a2c2a]"
          strokeWidth="3"
        />
        <path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke={color || "#1F6B4A"}
          strokeWidth="3"
          strokeDasharray={`${value}, 100`}
          strokeLinecap="round"
        />
      </svg>
      <span className="tabular absolute inset-0 flex items-center justify-center text-xs font-semibold">
        {Math.round(value)}%
      </span>
    </div>
  );
}
