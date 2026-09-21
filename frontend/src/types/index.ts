export type Account = {
  id: number;
  name: string;
  institution: string;
  account_type: string;
  opening_balance: string;
  current_balance: string;
  currency: string;
  color: string;
  icon: string;
  notes: string;
  is_archived: boolean;
  include_in_net_worth: boolean;
  include_in_safe_to_spend: boolean;
  is_liability: boolean;
};

export type Category = {
  id: number;
  name: string;
  parent: number | null;
  icon: string;
  color: string;
  kind: string;
  sort_order: number;
  children?: Category[];
};

export type Transaction = {
  id: number;
  account: number;
  account_name: string;
  category: number | null;
  category_name: string | null;
  category_icon: string;
  category_color: string;
  amount: string;
  transaction_type: "income" | "expense" | "transfer";
  merchant: string;
  description: string;
  transaction_date: string;
  notes: string;
  payment_method: string;
  tag_ids?: number[];
  receipts?: { id: number; image: string; thumbnail: string | null }[];
};

export type SafeToSpend = {
  available: string;
  upcoming_bills: string;
  debt_payments: string;
  goal_reserve: string;
  emergency_reserve: string;
  savings_reserve: string;
  safe_to_spend: string;
  horizon_days: number;
};

export type Dashboard = {
  greeting: string;
  display_name: string;
  date: string;
  year: number;
  month: number;
  currency: string;
  currency_symbol: string;
  hide_balance: boolean;
  total_balance: string;
  balance_change_percent: string;
  safe_to_spend: SafeToSpend;
  month_overview: { income: string; expenses: string; saved: string; savings_rate: string };
  today: {
    spent_today: string;
    income_today: string;
    remaining_daily_allowance: string;
    daily_allowance: string;
  };
  spending_chart: {
    daily: { date: string; amount: string }[];
    weekly: { label: string; amount: string }[];
    monthly: { label: string; amount: string }[];
  };
  categories: {
    id: number | null;
    name: string;
    color: string;
    icon: string;
    total: string;
    count: number;
  }[];
  recent_transactions: Transaction[];
  upcoming_bills: { id: number; name: string; amount: string; due_date: string; status: string }[];
  budgets: null | {
    items: {
      category_name: string;
      allocated: string;
      spent: string;
      remaining: string;
      used_percent: string;
      insight: string;
      category_color: string;
    }[];
  };
  goals: { id: number; name: string; current_amount: string; target_amount: string; progress: string; color: string }[];
  net_worth: string;
  unread_notifications: number;
  subscription_monthly: string;
  insights: { id: string; tone: string; title: string; body: string }[];
};

export type Profile = {
  username: string;
  email: string;
  first_name: string;
  display_name: string;
  currency: string;
  currency_symbol: string;
  theme: "system" | "light" | "dark";
  hide_balance: boolean;
  pin_enabled: boolean;
  lock_after_minutes: number;
  emergency_reserve: string;
  savings_reserve: string;
  obligation_horizon_days: number;
  include_upcoming_bills: boolean;
  include_debt_payments: boolean;
  include_goal_reserves: boolean;
  daily_spending_period_days: number;
  notify_bills: boolean;
  notify_budgets: boolean;
  notify_subscriptions: boolean;
  notify_goals: boolean;
  notify_unusual: boolean;
  ai_enabled: boolean;
};
