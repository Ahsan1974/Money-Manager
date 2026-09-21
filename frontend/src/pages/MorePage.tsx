import { useNavigate } from "react-router-dom";
import {
  Calculator,
  CreditCard,
  FileText,
  Handshake,
  Landmark,
  PieChart,
  Repeat,
  Settings,
  Sparkles,
  Target,
  TrendingUp,
  Wallet,
} from "lucide-react";

const ITEMS = [
  { to: "/app/accounts", label: "Accounts", icon: Landmark },
  { to: "/app/categories", label: "Categories", icon: Wallet },
  { to: "/app/budgets", label: "Budgets", icon: PieChart },
  { to: "/app/goals", label: "Goals", icon: Target },
  { to: "/app/bills", label: "Bills", icon: FileText },
  { to: "/app/subscriptions", label: "Subscriptions", icon: Repeat },
  { to: "/app/debts", label: "Debts", icon: CreditCard },
  { to: "/app/lending", label: "Lending", icon: Handshake },
  { to: "/app/net-worth", label: "Net worth", icon: TrendingUp },
  { to: "/app/investments", label: "Investments", icon: Wallet },
  { to: "/app/reports", label: "Reports", icon: FileText },
  { to: "/app/calculator", label: "Calculators", icon: Calculator },
  { to: "/app/assistant", label: "Assistant", icon: Sparkles },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export function MorePage() {
  const navigate = useNavigate();
  return (
    <div>
      <h1 className="mb-4 font-display text-3xl">More</h1>
      <div className="divide-y divide-paper-line dark:divide-[#2a2c2a]">
        {ITEMS.map((item) => (
          <button key={item.to} onClick={() => navigate(item.to)} className="flex min-h-14 w-full items-center gap-3 text-left">
            <item.icon className="h-4 w-4" />
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
}
