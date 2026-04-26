"use client";

import { useQuery } from "@tanstack/react-query";
import { suppliersApi } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/Badge";
import { formatNumber } from "@/lib/utils";
import { Users, Trophy, Plus } from "lucide-react";
import type { Supplier, PaginatedResponse, SupplierRank } from "@/types";

function ScoreBar({ value, max = 1 }: { value: number; max?: number }) {
  const pct = (value / max) * 100;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-surface rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-brand-600 to-emerald-400 rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-10 text-right">{(value * 100).toFixed(0)}</span>
    </div>
  );
}

export default function SuppliersPage() {
  const { data, isLoading } = useQuery<PaginatedResponse<Supplier>>({
    queryKey: ["suppliers"],
    queryFn: () => suppliersApi.list({ page: 1, page_size: 50 }).then((r) => r.data),
  });

  const { data: rankings } = useQuery<SupplierRank[]>({
    queryKey: ["supplier-rankings"],
    queryFn: () => suppliersApi.rankings().then((r) => r.data),
  });

  const columns = [
    { key: "code", header: "Code", render: (s: Supplier) => <span className="font-mono text-xs text-brand-400">{s.code}</span> },
    { key: "name", header: "Name", render: (s: Supplier) => <span className="font-medium text-white">{s.name}</span> },
    { key: "country", header: "Country", render: (s: Supplier) => <span className="text-slate-400">{s.country ?? "—"}</span> },
    { key: "status", header: "Status", render: (s: Supplier) => <StatusBadge status={s.status} /> },
    { key: "lead_time_days", header: "Lead Time", render: (s: Supplier) => <span>{s.lead_time_days}d</span> },
    {
      key: "on_time_delivery_rate", header: "On-Time",
      render: (s: Supplier) => <ScoreBar value={s.on_time_delivery_rate} />,
    },
    {
      key: "quality_score", header: "Quality",
      render: (s: Supplier) => <ScoreBar value={s.quality_score} />,
    },
    {
      key: "composite_score", header: "Score",
      render: (s: Supplier) => (
        <span className={`font-mono text-xs font-bold ${s.composite_score > 0.7 ? "text-emerald-400" : s.composite_score > 0.4 ? "text-yellow-400" : "text-red-400"}`}>
          {(s.composite_score * 100).toFixed(1)}
        </span>
      ),
    },
    { key: "total_orders", header: "Orders", render: (s: Supplier) => formatNumber(s.total_orders) },
  ];

  return (
    <div className="animate-fade-in">
      <Header title="Suppliers" subtitle="Vendor management & performance tracking" />

      <div className="p-6 space-y-6">

        {/* Rankings Summary */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <Trophy className="w-5 h-5 text-yellow-400" />
            <div>
              <h3 className="font-semibold text-white">Supplier Rankings</h3>
              <p className="text-xs text-slate-500">Weighted multi-factor scoring — Merge Sort ranked</p>
            </div>
          </div>
          <div className="grid grid-cols-5 gap-3">
            {(rankings ?? []).slice(0, 5).map((s) => (
              <div key={s.supplier_id} className={`p-3 rounded-xl border ${s.rank === 1 ? "border-yellow-400/30 bg-yellow-400/5" : "border-surface-border"}`}>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-xs font-bold ${s.rank === 1 ? "text-yellow-400" : s.rank === 2 ? "text-slate-400" : s.rank === 3 ? "text-amber-700" : "text-slate-500"}`}>
                    #{s.rank}
                  </span>
                  <span className="text-xs font-medium text-white truncate">{s.name}</span>
                </div>
                <div className="text-2xl font-bold text-white mb-2">{(s.composite_score * 100).toFixed(0)}</div>
                <div className="space-y-1">
                  {Object.entries(s.breakdown).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs">
                      <span className="text-slate-500 capitalize">{k.replace("_", " ")}</span>
                      <span className="text-slate-300">{(Number(v) * 100).toFixed(0)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Supplier Table */}
        <div className="flex justify-between items-center">
          <h3 className="font-semibold text-white">All Suppliers</h3>
          <button className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Supplier
          </button>
        </div>
        <div className="card p-0 overflow-hidden">
          <DataTable
            columns={columns as never}
            data={(data?.items ?? []) as never}
            loading={isLoading}
            rowKey={(s) => (s as Supplier).id}
            emptyMessage="No suppliers found"
          />
        </div>
      </div>
    </div>
  );
}
