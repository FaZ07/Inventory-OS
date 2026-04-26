import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: { value: number; label: string };
  color?: "blue" | "green" | "yellow" | "red" | "purple";
  loading?: boolean;
}

const COLOR_MAP = {
  blue: { icon: "text-blue-400", bg: "bg-blue-400/10", border: "border-blue-400/20" },
  green: { icon: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/20" },
  yellow: { icon: "text-yellow-400", bg: "bg-yellow-400/10", border: "border-yellow-400/20" },
  red: { icon: "text-red-400", bg: "bg-red-400/10", border: "border-red-400/20" },
  purple: { icon: "text-purple-400", bg: "bg-purple-400/10", border: "border-purple-400/20" },
};

export function KPICard({ title, value, subtitle, icon: Icon, trend, color = "blue", loading }: KPICardProps) {
  const colors = COLOR_MAP[color];

  if (loading) {
    return (
      <div className="card animate-pulse">
        <div className="h-4 w-24 bg-surface-hover rounded mb-3" />
        <div className="h-8 w-16 bg-surface-hover rounded mb-2" />
        <div className="h-3 w-20 bg-surface-hover rounded" />
      </div>
    );
  }

  return (
    <div className={cn("card border", colors.border, "hover:border-opacity-60 transition-all group")}>
      <div className="flex items-start justify-between mb-4">
        <p className="text-sm text-slate-400 font-medium">{title}</p>
        <div className={cn("p-2 rounded-lg", colors.bg)}>
          <Icon className={cn("w-4 h-4", colors.icon)} />
        </div>
      </div>
      <p className="text-2xl font-bold text-white mb-1">{value}</p>
      {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      {trend && (
        <div className="flex items-center gap-1 mt-2">
          <span className={cn("text-xs font-medium", trend.value >= 0 ? "text-emerald-400" : "text-red-400")}>
            {trend.value >= 0 ? "+" : ""}{trend.value}%
          </span>
          <span className="text-xs text-slate-500">{trend.label}</span>
        </div>
      )}
    </div>
  );
}
