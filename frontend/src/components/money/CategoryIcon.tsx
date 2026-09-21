import {
  Banknote,
  Bike,
  Briefcase,
  Car,
  Circle,
  Clapperboard,
  CreditCard,
  Fuel,
  Gift,
  GraduationCap,
  HeartPulse,
  Landmark,
  Laptop,
  PiggyBank,
  Plane,
  PlusCircle,
  Receipt,
  Repeat,
  Shield,
  ShoppingBag,
  ShoppingBasket,
  Smartphone,
  Utensils,
  UtensilsCrossed,
  Wallet,
  Wrench,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/utils/cn";

const ICONS: Record<string, LucideIcon> = {
  utensils: Utensils,
  "utensils-crossed": UtensilsCrossed,
  bike: Bike,
  car: Car,
  "car-front": Car,
  fuel: Fuel,
  wrench: Wrench,
  receipt: Receipt,
  "shopping-bag": ShoppingBag,
  "shopping-basket": ShoppingBasket,
  clapperboard: Clapperboard,
  "heart-pulse": HeartPulse,
  "graduation-cap": GraduationCap,
  plane: Plane,
  repeat: Repeat,
  circle: Circle,
  banknote: Banknote,
  briefcase: Briefcase,
  gift: Gift,
  "plus-circle": PlusCircle,
  wallet: Wallet,
  landmark: Landmark,
  "piggy-bank": PiggyBank,
  smartphone: Smartphone,
  "credit-card": CreditCard,
  laptop: Laptop,
  shield: Shield,
};

export function CategoryIcon({
  name,
  color,
  className,
}: {
  name?: string | null;
  color?: string;
  className?: string;
}) {
  const Icon = ICONS[name || "circle"] || Circle;
  return (
    <span
      className={cn("flex h-10 w-10 items-center justify-center rounded-2xl", className)}
      style={{ background: `${color || "#6B7280"}22`, color: color || "#6B7280" }}
    >
      <Icon className="h-4 w-4" />
    </span>
  );
}
