"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Package, Warehouse, Users, ShoppingCart,
  Truck, BarChart3, Settings, LogOut, Zap, Bell,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/inventory", label: "Inventory", icon: Package },
  { href: "/warehouses", label: "Warehouses", icon: Warehouse },
  { href: "/suppliers", label: "Suppliers", icon: Users },
  { href: "/orders", label: "Orders", icon: ShoppingCart },
  { href: "/shipments", label: "Shipments", icon: Truck },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  return (
    <aside className="w-64 flex flex-col h-screen bg-surface-card border-r border-surface-border fixed left-0 top-0 z-30">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-surface-border">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-white text-sm">InventoryOS</h1>
          <p className="text-xs text-slate-500">Supply Chain Platform</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-brand-600/20 text-brand-400 border border-brand-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-surface-hover"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom user */}
      <div className="px-3 py-4 border-t border-surface-border space-y-1">
        <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-slate-200 hover:bg-surface-hover w-full transition-colors">
          <Bell className="w-4 h-4" />
          Alerts
        </button>
        <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-slate-200 hover:bg-surface-hover w-full transition-colors">
          <Settings className="w-4 h-4" />
          Settings
        </button>
        {user && (
          <div className="flex items-center gap-3 px-3 py-2.5 mt-2">
            <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold text-white">
              {user.full_name[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white truncate">{user.full_name}</p>
              <p className="text-xs text-slate-500 capitalize">{user.role.replace("_", " ")}</p>
            </div>
            <button onClick={logout} className="text-slate-500 hover:text-red-400 transition-colors">
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
