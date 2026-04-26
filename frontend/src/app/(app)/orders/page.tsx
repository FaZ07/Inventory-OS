"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ordersApi } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/Badge";
import { formatCurrency, formatDate, formatNumber } from "@/lib/utils";
import { Zap, ShoppingCart, Plus } from "lucide-react";
import type { Order, PaginatedResponse } from "@/types";

export default function OrdersPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [orderType, setOrderType] = useState("");
  const [priority, setPriority] = useState("");
  const [showQueue, setShowQueue] = useState(false);

  const { data, isLoading } = useQuery<PaginatedResponse<Order>>({
    queryKey: ["orders", page, status, orderType, priority],
    queryFn: () => ordersApi.list({ page, page_size: 20, status: status || undefined, order_type: orderType || undefined, priority: priority || undefined }).then((r) => r.data),
    enabled: !showQueue,
  });

  const { data: queue, isLoading: queueLoading } = useQuery({
    queryKey: ["order-priority-queue"],
    queryFn: () => ordersApi.priorityQueue(20).then((r) => r.data),
    enabled: showQueue,
  });

  const columns = [
    { key: "order_number", header: "Order #", render: (o: Order) => <span className="font-mono text-xs text-brand-400">{o.order_number}</span> },
    { key: "order_type", header: "Type", render: (o: Order) => <StatusBadge status={o.order_type} /> },
    { key: "status", header: "Status", render: (o: Order) => <StatusBadge status={o.status} /> },
    { key: "priority", header: "Priority", render: (o: Order) => <StatusBadge status={o.priority} /> },
    { key: "total_amount", header: "Total", render: (o: Order) => <span className="text-emerald-400">{formatCurrency(o.total_amount)}</span> },
    { key: "items", header: "Items", render: (o: Order) => <span>{o.items.length}</span> },
    { key: "expected_delivery", header: "Due", render: (o: Order) => o.expected_delivery ? <span className="text-xs">{formatDate(o.expected_delivery)}</span> : <span className="text-slate-500">—</span> },
    { key: "created_at", header: "Created", render: (o: Order) => <span className="text-xs text-slate-500">{formatDate(o.created_at)}</span> },
  ];

  return (
    <div className="animate-fade-in">
      <Header title="Orders" subtitle="Purchase, sales & transfer order management" />

      <div className="p-6 space-y-4">

        {/* Toolbar */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="input w-36">
              <option value="">All Statuses</option>
              {["draft","pending","approved","processing","shipped","delivered","cancelled"].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <select value={orderType} onChange={(e) => setOrderType(e.target.value)} className="input w-36">
              <option value="">All Types</option>
              {["purchase","sales","transfer","return"].map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <select value={priority} onChange={(e) => setPriority(e.target.value)} className="input w-32">
              <option value="">All Priority</option>
              {["critical","high","medium","low"].map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
            <button
              onClick={() => setShowQueue((v) => !v)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${showQueue ? "bg-yellow-400/20 text-yellow-400 border border-yellow-400/30" : "btn-secondary"}`}
            >
              <Zap className="w-4 h-4" />
              Priority Queue
            </button>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Order
          </button>
        </div>

        {showQueue ? (
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-yellow-400" />
              <h3 className="font-semibold text-white">Order Priority Queue</h3>
              <span className="text-xs text-slate-500">— Binary Heap ranked by urgency score</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-border text-left">
                    <th className="pb-3 px-3 text-xs text-slate-400 uppercase">Order #</th>
                    <th className="pb-3 px-3 text-xs text-slate-400 uppercase">Priority</th>
                    <th className="pb-3 px-3 text-xs text-slate-400 uppercase">Status</th>
                    <th className="pb-3 px-3 text-xs text-slate-400 uppercase">Value</th>
                    <th className="pb-3 px-3 text-xs text-slate-400 uppercase">Days Overdue</th>
                    <th className="pb-3 px-3 text-xs text-slate-400 uppercase text-right">Urgency Score</th>
                  </tr>
                </thead>
                <tbody>
                  {queueLoading ? (
                    <tr><td colSpan={6} className="py-8 text-center text-slate-500">Loading…</td></tr>
                  ) : (queue ?? []).map((o: { order_id: number; order_number: string; priority: string; status: string; total_value: number; days_overdue: number; urgency_score: number }, idx: number) => (
                    <tr key={o.order_id} className="border-b border-surface-border/50 hover:bg-surface-hover/20">
                      <td className="py-3 px-3">
                        <span className="text-xs text-slate-500 mr-2">#{idx + 1}</span>
                        <span className="font-mono text-xs text-brand-400">{o.order_number}</span>
                      </td>
                      <td className="py-3 px-3"><StatusBadge status={o.priority} /></td>
                      <td className="py-3 px-3"><StatusBadge status={o.status} /></td>
                      <td className="py-3 px-3 text-emerald-400">{formatCurrency(o.total_value)}</td>
                      <td className="py-3 px-3">
                        {o.days_overdue > 0 ? (
                          <span className="text-red-400 font-medium">{o.days_overdue.toFixed(0)}d</span>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <span className="font-mono text-xs bg-yellow-400/10 text-yellow-400 px-2 py-0.5 rounded">
                          {o.urgency_score.toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="card p-0 overflow-hidden">
            <DataTable
              columns={columns as never}
              data={(data?.items ?? []) as never}
              loading={isLoading}
              rowKey={(o) => (o as Order).id}
              emptyMessage="No orders found"
            />
            {data && data.total_pages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-surface-border">
                <p className="text-xs text-slate-500">Total: {formatNumber(data.total)} orders</p>
                <div className="flex items-center gap-2">
                  <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-xs px-3 py-1.5 disabled:opacity-40">Prev</button>
                  <span className="text-xs text-slate-400">{page} / {data.total_pages}</span>
                  <button onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))} disabled={page === data.total_pages} className="btn-secondary text-xs px-3 py-1.5 disabled:opacity-40">Next</button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
