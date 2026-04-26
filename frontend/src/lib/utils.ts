import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(amount);
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat("en-US").format(n);
}

export function formatPercent(n: number, decimals = 1): string {
  return `${n.toFixed(decimals)}%`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export const STATUS_COLORS: Record<string, string> = {
  active: "text-emerald-400 bg-emerald-400/10",
  delivered: "text-emerald-400 bg-emerald-400/10",
  completed: "text-emerald-400 bg-emerald-400/10",
  pending: "text-yellow-400 bg-yellow-400/10",
  processing: "text-blue-400 bg-blue-400/10",
  in_transit: "text-blue-400 bg-blue-400/10",
  approved: "text-blue-400 bg-blue-400/10",
  critical: "text-red-400 bg-red-400/10",
  cancelled: "text-gray-400 bg-gray-400/10",
  delayed: "text-orange-400 bg-orange-400/10",
  blacklisted: "text-red-400 bg-red-400/10",
  maintenance: "text-yellow-400 bg-yellow-400/10",
  high: "text-orange-400 bg-orange-400/10",
  medium: "text-yellow-400 bg-yellow-400/10",
  low: "text-gray-400 bg-gray-400/10",
};

export function statusBadge(status: string): string {
  return STATUS_COLORS[status] ?? "text-gray-400 bg-gray-400/10";
}
