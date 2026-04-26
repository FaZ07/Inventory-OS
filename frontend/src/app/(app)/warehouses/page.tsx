"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { warehousesApi } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { StatusBadge } from "@/components/ui/Badge";
import { formatNumber, formatPercent } from "@/lib/utils";
import { Warehouse, MapPin, Navigation, Zap, Plus } from "lucide-react";
import toast from "react-hot-toast";

export default function WarehousesPage() {
  const [selectedWh, setSelectedWh] = useState<number | null>(null);
  const [origin, setOrigin] = useState("");
  const [dest, setDest] = useState("");
  const [routeResult, setRouteResult] = useState<unknown>(null);

  const { data: warehouses = [], isLoading } = useQuery({
    queryKey: ["warehouses"],
    queryFn: () => warehousesApi.list().then((r) => r.data),
  });

  const { data: stock, isLoading: stockLoading } = useQuery({
    queryKey: ["warehouse-stock", selectedWh],
    queryFn: () => warehousesApi.stock(selectedWh!).then((r) => r.data),
    enabled: !!selectedWh,
  });

  const routeMutation = useMutation({
    mutationFn: (data: { origin_warehouse_id: number; destination_warehouse_id: number }) =>
      warehousesApi.optimizeRoute(data).then((r) => r.data),
    onSuccess: (data) => {
      setRouteResult(data);
      toast.success("Route optimized via Dijkstra's algorithm");
    },
    onError: () => toast.error("Route optimization failed"),
  });

  const handleRouteOptimize = () => {
    if (!origin || !dest) { toast.error("Select origin and destination"); return; }
    routeMutation.mutate({ origin_warehouse_id: +origin, destination_warehouse_id: +dest });
  };

  return (
    <div className="animate-fade-in">
      <Header title="Warehouses" subtitle="Facility management & route optimization" />

      <div className="p-6 space-y-6">

        {/* Warehouse Grid */}
        <div className="grid grid-cols-3 gap-4">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="card animate-pulse h-48" />
            ))
          ) : (warehouses as Array<{ id: number; name: string; code: string; city: string; country: string; status: string; current_utilization_pct: number; capacity_sqft: number; manager_name?: string }>).map((wh) => (
            <button key={wh.id}
              onClick={() => setSelectedWh(wh.id === selectedWh ? null : wh.id)}
              className={`card text-left transition-all hover:border-brand-500/50 ${selectedWh === wh.id ? "border-brand-500" : ""}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="p-2 bg-blue-400/10 rounded-lg">
                  <Warehouse className="w-4 h-4 text-blue-400" />
                </div>
                <StatusBadge status={wh.status} />
              </div>
              <h3 className="font-semibold text-white mb-1">{wh.name}</h3>
              <p className="text-xs text-slate-500 mb-3 flex items-center gap-1">
                <MapPin className="w-3 h-3" /> {wh.city}, {wh.country}
              </p>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Utilization</span>
                  <span className={wh.current_utilization_pct > 85 ? "text-red-400" : "text-slate-300"}>
                    {formatPercent(wh.current_utilization_pct)}
                  </span>
                </div>
                <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${wh.current_utilization_pct > 85 ? "bg-red-500" : wh.current_utilization_pct > 60 ? "bg-yellow-500" : "bg-emerald-500"}`}
                    style={{ width: `${wh.current_utilization_pct}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Capacity</span>
                  <span className="text-slate-300">{formatNumber(wh.capacity_sqft)} sqft</span>
                </div>
                {wh.manager_name && (
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Manager</span>
                    <span className="text-slate-300 truncate ml-2">{wh.manager_name}</span>
                  </div>
                )}
              </div>
            </button>
          ))}
          <button className="card border-dashed border-2 flex flex-col items-center justify-center gap-2 text-slate-500 hover:text-slate-300 hover:border-slate-500 transition-colors h-48">
            <Plus className="w-6 h-6" />
            <span className="text-sm">Add Warehouse</span>
          </button>
        </div>

        {/* Route Optimizer (Dijkstra) */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <Navigation className="w-5 h-5 text-blue-400" />
            <div>
              <h3 className="font-semibold text-white">Route Optimizer</h3>
              <p className="text-xs text-slate-500">Dijkstra's shortest path + bottleneck detection</p>
            </div>
            <span className="badge text-blue-400 bg-blue-400/10 border border-blue-400/20 text-xs">Dijkstra's O((V+E)logV)</span>
          </div>
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="text-xs text-slate-400 mb-1 block">Origin Warehouse</label>
              <select value={origin} onChange={(e) => setOrigin(e.target.value)} className="input">
                <option value="">Select origin…</option>
                {(warehouses as Array<{ id: number; name: string; code: string }>).map((w) => (
                  <option key={w.id} value={w.id}>{w.code} — {w.name}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="text-xs text-slate-400 mb-1 block">Destination Warehouse</label>
              <select value={dest} onChange={(e) => setDest(e.target.value)} className="input">
                <option value="">Select destination…</option>
                {(warehouses as Array<{ id: number; name: string; code: string }>).map((w) => (
                  <option key={w.id} value={w.id}>{w.code} — {w.name}</option>
                ))}
              </select>
            </div>
            <button onClick={handleRouteOptimize} disabled={routeMutation.isPending}
              className="btn-primary flex items-center gap-2 whitespace-nowrap">
              <Zap className="w-4 h-4" />
              {routeMutation.isPending ? "Optimizing…" : "Find Optimal Route"}
            </button>
          </div>

          {routeResult && (
            <div className="mt-4 p-4 bg-surface rounded-xl border border-brand-500/20 animate-slide-up">
              <h4 className="text-sm font-semibold text-brand-400 mb-3">Optimal Route Found</h4>
              <div className="grid grid-cols-4 gap-4 mb-4">
                <div><p className="text-xs text-slate-500">Total Cost</p><p className="text-white font-bold">${(routeResult as { total_cost: number }).total_cost.toFixed(2)}</p></div>
                <div><p className="text-xs text-slate-500">Distance</p><p className="text-white font-bold">{(routeResult as { total_distance_km: number }).total_distance_km} km</p></div>
                <div><p className="text-xs text-slate-500">Est. Days</p><p className="text-white font-bold">{(routeResult as { estimated_days: number }).estimated_days}d</p></div>
                <div><p className="text-xs text-slate-500">Hops</p><p className="text-white font-bold">{(routeResult as { hops: number }).hops}</p></div>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {((routeResult as { path_names?: string[] }).path_names ?? []).map((name: string, i: number, arr: string[]) => (
                  <span key={i} className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-brand-600/20 text-brand-400 rounded text-xs border border-brand-600/30">{name}</span>
                    {i < arr.length - 1 && <span className="text-slate-500">→</span>}
                  </span>
                ))}
              </div>
              {((routeResult as { network_bottlenecks?: number[] }).network_bottlenecks ?? []).length > 0 && (
                <p className="mt-3 text-xs text-yellow-400">
                  ⚠ Bottleneck nodes detected: {(routeResult as { network_bottlenecks: number[] }).network_bottlenecks.join(", ")}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Stock Detail */}
        {selectedWh && (
          <div className="card animate-slide-up">
            <h3 className="font-semibold text-white mb-4">Stock — Warehouse #{selectedWh}</h3>
            {stockLoading ? (
              <div className="text-slate-500 text-sm">Loading stock…</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-surface-border">
                      {["SKU", "Product", "Category", "Qty", "Reserved", "Available", "Reorder Pt", "Needs Reorder"].map((h) => (
                        <th key={h} className="text-left py-2 px-3 text-xs text-slate-400 uppercase">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(stock as Array<{ sku: string; name: string; category: string; quantity: number; reserved_quantity: number; available: number; reorder_point: number; needs_reorder: boolean; product_id: number }> ?? []).map((s) => (
                      <tr key={s.product_id} className="border-b border-surface-border/50 hover:bg-surface-hover/20">
                        <td className="py-2 px-3 font-mono text-xs text-brand-400">{s.sku}</td>
                        <td className="py-2 px-3 text-slate-300">{s.name}</td>
                        <td className="py-2 px-3"><StatusBadge status={s.category} /></td>
                        <td className="py-2 px-3">{formatNumber(s.quantity)}</td>
                        <td className="py-2 px-3 text-slate-500">{s.reserved_quantity}</td>
                        <td className="py-2 px-3 text-emerald-400">{formatNumber(s.available)}</td>
                        <td className="py-2 px-3 text-slate-400">{s.reorder_point}</td>
                        <td className="py-2 px-3">
                          {s.needs_reorder ? (
                            <span className="badge text-red-400 bg-red-400/10">Reorder</span>
                          ) : (
                            <span className="text-slate-500 text-xs">OK</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
