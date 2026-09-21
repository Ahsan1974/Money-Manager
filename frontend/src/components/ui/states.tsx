import { Inbox } from "lucide-react";
import { Button } from "@/components/ui/primitives";
import { cn } from "@/utils/cn";

export function EmptyState({
  title,
  body,
  action,
  onAction,
}: {
  title: string;
  body: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex flex-col items-center px-6 py-14 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-forest-soft text-forest dark:bg-[#1a2a22]">
        <Inbox className="h-5 w-5" />
      </div>
      <h3 className="font-display text-xl">{title}</h3>
      <p className="mt-2 max-w-xs text-sm text-ink-muted">{body}</p>
      {action && (
        <Button className="mt-5" onClick={onAction}>
          {action}
        </Button>
      )}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-2xl bg-paper-line/70 dark:bg-[#2a2c2a]", className)} />;
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-4 p-4">
      <Skeleton className="h-8 w-40" />
      <Skeleton className="h-40 w-full" />
      <div className="grid grid-cols-2 gap-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-48 w-full" />
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-16 w-full" />
    </div>
  );
}
