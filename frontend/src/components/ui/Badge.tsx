import { cn, statusBadge } from "@/lib/utils";

interface BadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: BadgeProps) {
  return (
    <span className={cn("badge", statusBadge(status), className)}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

interface SimpleBadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info";
  className?: string;
}

const VARIANT_CLASSES = {
  default: "text-slate-300 bg-slate-700/50",
  success: "text-emerald-400 bg-emerald-400/10",
  warning: "text-yellow-400 bg-yellow-400/10",
  danger: "text-red-400 bg-red-400/10",
  info: "text-blue-400 bg-blue-400/10",
};

export function Badge({ children, variant = "default", className }: SimpleBadgeProps) {
  return (
    <span className={cn("badge", VARIANT_CLASSES[variant], className)}>
      {children}
    </span>
  );
}
