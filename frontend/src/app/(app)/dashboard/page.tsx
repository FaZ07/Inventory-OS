"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Package, Warehouse, Users, DollarSign, ShoppingCart,
  Truck, AlertTriangle, Activity, TrendingUp, Zap,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, RadialBarChart, RadialBar, Legend,
} from "recharts";
import { analyticsApi } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { KPICard } from "@/components/ui/KPICard";
import { StatusBadge } from "@/components/ui/Badge";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import type { DashboardKPIs, RestockItem } from "@/types";

const CHART_THEME = {
  grid: "#334155",
  text: "#94a3b8",
  primary: "#3b82f6",
  secondary: "#10b981",
  accent: "#f59e0b",
};

export default function DashboardPage() {
  const { data: kpis, isLoading: kpiLoading } = useQuery<DashboardKPIs>({
    queryKey: ["dashboard-kpis"],
    queryFn: () => analyticsApi.dashboard().then((r) => r.data),
    refetchInterval: 30_000,
  });

  const { data: revenueTrend } = useQuery({
    queryKey: ["revenue-trend-30"],
    queryFn: () => analyticsApi.revenueTrend(30).then((r) => r.data),
  });

  const { data: utilization } = useQuery({
    queryKey: ["warehouse-utilization"],
    queryFn: () => analyticsApi.warehouseUtilization().then((r) => r.data),
  });

  const { data: restockQueue } = useQuery<RestockItem[]>({
    queryKey: ["restock-queue"],
    queryFn: () => analyticsApi.restockQueue().then((r) => r.data),
  });

  const { data: topProducts } = useQuery({
    queryKey: ["top-products"],
    queryFn: () => analyticsApi.topProducts(5).then((r) => r.data),
  });

  const { data: health } = useQuery({
    queryKey: ["supply-chain-health"],
    queryFn: () => analyticsApi.supplyChainHealth().then((r) => r.data),
  });

  return (
    <div className="animate-fade-in">
      <Header title="Dashboard" subtitle="Real-time supply chain intelligence" />

      <div className="p-6 space-y-6">

        {/* KPI Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard title="Monthly Revenue" value={formatCurrency(kpis?.monthly_revenue ?? 0)}
            icon={DollarSign} color="green" loading={kpiLoading}
            subtitle="Current month delivered" />
          <KPICard title="Total Products" value={formatNumber(kpis?.total_products ?? 0)}
            icon={Package} color="blue" loading={kpiLoading}
            subtitle={`${kpis?.low_stock_alerts ?? 0} low stock alerts`} />
          <KPICard title="Active Shipments" value={formatNumber(kpis?.active_shipments ?? 0)}
            icon={Truck} color="purple" loading={kpiLoading}
            subtitle="In transit" />
          <KPICard title="Pending Orders" value={formatNumber(kpis?.pending_orders ?? 0)}
            icon={ShoppingCart} color="yellow" loading={kpiLoading}
            subtitle="Awaiting fulfillment" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard title="Warehouses" value={kpis?.total_warehouses ?? 0}
            icon={Warehouse} color="blue" loading={kpiLoading} />
          <KPICard title="Suppliers" value={kpis?.total_suppliers ?? 0}
            icon={Users} color="green" loading={kpiLoading} />
          <KPICard title="Low Stock Alerts" value={kpis?.low_stock_alerts ?? 0}
            icon={AlertTriangle} color="red" loading={kpiLoading} />
          <KPICard title="Avg Utilization" value={formatPercent(kpis?.avg_warehouse_utilization_pct ?? 0)}
            icon={Activity} color="purple" loading={kpiLoading} />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-3 gap-6">

          {/* Revenue Trend */}
          <div className="col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-white">Revenue Trend (30d)</h3>
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={revenueTrend ?? []}>
                <defs>
                  <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_THEME.secondary} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_THEME.secondary} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_THEME.grid} />
                <XAxis dataKey="date" stroke={CHART_THEME.text} tick={{ fontSize: 11 }} />
                <YAxis stroke={CHART_THEME.text} tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                  formatter={(v: number) => [formatCurrency(v), "Revenue"]}
                />
                <Area type="monotone" dataKey="revenue" stroke={CHART_THEME.secondary} fill="url(#revenueGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Supply Chain Health */}
          <div className="card flex flex-col">
            <h3 className="font-semibold text-white mb-4">Supply Chain Health</h3>
            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="relative w-32 h-32">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#334155" strokeWidth="10" />
                  <circle
                    cx="50" cy="50" r="40" fill="none"
                    stroke={health?.health_score > 70 ? "#10b981" : health?.health_score > 40 ? "#f59e0b" : "#ef4444"}
                    strokeWidth="10"
                    strokeDasharray={`${(health?.health_score ?? 0) * 2.51} 251`}
                    strokeLinecap="round"
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold text-white">{health?.health_score?.toFixed(0) ?? "—"}</span>
                  <span className="text-xs text-slate-500">/ 100</span>
                </div>
              </div>
              <div className="mt-4 space-y-2 w-full">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">On-time rate</span>
                  <span className="text-white">{health?.on_time_delivery_rate_pct ?? 0}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Total delivered</span>
                  <span className="text-white">{formatNumber(health?.total_delivered ?? 0)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Currently delayed</span>
                  <span className="text-red-400">{health?.currently_delayed ?? 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Row */}
        <div className="grid grid-cols-2 gap-6">

          {/* Warehouse Utilization */}
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Warehouse Utilization</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={utilization ?? []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_THEME.grid} horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} stroke={CHART_THEME.text} tickFormatter={(v) => `${v}%`} />
                <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 11 }} stroke={CHART_THEME.text} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                  formatter={(v: number) => [`${v}%`, "Utilization"]}
                />
                <Bar dataKey="utilization_pct" fill={CHART_THEME.primary} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Restock Queue (DSA: RestockHeap) */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-white">Restock Queue</h3>
              <div className="flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-yellow-400" />
                <span className="text-xs text-slate-500">Binary Heap ranked</span>
              </div>
            </div>
            <div className="space-y-2">
              {(restockQueue ?? []).slice(0, 6).map((item) => (
                <div key={`${item.product_id}-${item.warehouse_id}`}
                  className="flex items-center justify-between py-2 border-b border-surface-border/50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-white">{item.sku}</p>
                    <p className="text-xs text-slate-500">{item.name.slice(0, 30)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium text-red-400">{item.days_until_stockout}d left</p>
                    <p className="text-xs text-slate-500">{item.current_stock} in stock</p>
                  </div>
                </div>
              ))}
              {(!restockQueue || restockQueue.length === 0) && (
                <p className="text-sm text-slate-500 text-center py-4">No restock alerts</p>
              )}
            </div>
          </div>
        </div>

        {/* Top Products */}
        <div className="card">
          <h3 className="font-semibold text-white mb-4">Top Products by Revenue</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border text-left">
                  <th className="pb-3 px-2 text-xs text-slate-400 uppercase">SKU</th>
                  <th className="pb-3 px-2 text-xs text-slate-400 uppercase">Name</th>
                  <th className="pb-3 px-2 text-xs text-slate-400 uppercase">Category</th>
                  <th className="pb-3 px-2 text-xs text-slate-400 uppercase text-right">Revenue</th>
                  <th className="pb-3 px-2 text-xs text-slate-400 uppercase text-right">Units Sold</th>
                </tr>
              </thead>
              <tbody>
                {(topProducts ?? []).map((p: { sku: string; name: string; category: string; total_revenue: number; total_units_sold: number }, idx: number) => (
                  <tr key={p.sku} className="border-b border-surface-border/50 hover:bg-surface-hover/20">
                    <td className="py-3 px-2">
                      <span className="text-xs text-slate-500 mr-2">#{idx + 1}</span>
                      <span className="font-mono text-brand-400 text-xs">{p.sku}</span>
                    </td>
                    <td className="py-3 px-2 text-slate-300">{p.name}</td>
                    <td className="py-3 px-2"><StatusBadge status={p.category} /></td>
                    <td className="py-3 px-2 text-right font-medium text-emerald-400">{formatCurrency(p.total_revenue)}</td>
                    <td className="py-3 px-2 text-right text-slate-300">{formatNumber(p.total_units_sold)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
