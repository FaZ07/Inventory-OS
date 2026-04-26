"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { shipmentsApi } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";
import { Truck, AlertTriangle, Zap } from "lucide-react";
import type { Shipment, PaginatedResponse } from "@/types";

export default function ShipmentsPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [showRisk, setShowRisk] = useState(false);

  const { data, isLoading } = useQuery<PaginatedResponse<Shipment>>({
    queryKey: ["shipments", page, status],
    queryFn: () => shipmentsApi.list({ page, page_size: 20, status: status || undefined }).then((r) => r.data),
    enabled: !showRisk,
  });

  const { data: riskQueue } = useQuery({
    queryKey: ["shipment-delay-risk"],
    queryFn: () => shipmentsApi.delayRisk().then((r) => r.data),
    enabled: showRisk,
  });

  const columns = [
    {
      key: "tracking_number", header: "Tracking",
      render: (s: Shipment) => <span className="font-mono text-xs text-brand-400">{s.tracking_number}</span>,
    },
    { key: "carrier", header: "Carrier", render: (s: Shipment) => <StatusBadge status={s.carrier} /> },
    { key: "status", header: "Status", render: (s: Shipment) => <StatusBadge status={s.status} /> },
    { key: "weight_kg", header: "Weight", render: (s: Shipment) => s.weight_kg ? `${s.weight_kg} kg` : "—" },
    { key: "route_distance_km", header: "Distance", render: (s: Shipment) => s.route_distance_km ? `${s.route_distance_km} km` : "—" },
    {
      key: "estimated_arrival", header: "ETA",
      render: (s: Shipment) => s.estimated_arrival ? formatDate(s.estimated_arrival) : "—",
    },
    { key: "events", header: "Events", render: (s: Shipment) => s.events.length },
    {
      key: "created_at", header: "Created",
      render: (s: Shipment) => <span className="text-xs text-slate-500">{formatDate(s.created_at)}</span>,
    },
  ];

  return (
    <div className="animate-fade-in">
      <Header title="Shipments" subtitle="Logistics tracking & delay risk monitoring" />

      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="input w-44">
              <option value="">All Statuses</option>
              {["pending","picked_up","in_transit","out_for_delivery","delivered","delayed","failed"].map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
              ))}
            </select>
            <button
              onClick={() => setShowRisk((v) => !v)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${showRisk ? "bg-red-400/20 text-red-400 border border-red-400/30" : "btn-secondary"}`}
            >
              <Zap className="w-4 h-4" />
              Delay Risk Queue
            </button>
          </div>
        </div>

        {showRisk ? (
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <h3 className="font-semibold text-white">Shipment Delay Risk</h3>
              <span className="text-xs text-slate-500">— ShipmentRiskHeap ranked by delay score</span>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border text-left">
                  {["Rank", "Tracking", "Carrier", "Status", "Days Delayed", "Risk Score"].map((h) => (
                    <th key={h} className="pb-3 px-3 text-xs text-slate-400 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(riskQueue ?? []).map((r: { shipment_id: number; tracking_number: string; carrier: string; status: string; days_delayed: number; risk_score: number }, i: number) => (
                  <tr key={r.shipment_id} className="border-b border-surface-border/50 hover:bg-surface-hover/20">
                    <td className="py-3 px-3 text-slate-500 text-xs">#{i + 1}</td>
                    <td className="py-3 px-3 font-mono text-xs text-brand-400">{r.tracking_number}</td>
                    <td className="py-3 px-3"><StatusBadge status={r.carrier} /></td>
                    <td className="py-3 px-3"><StatusBadge status={r.status} /></td>
                    <td className="py-3 px-3">
                      <span className={r.days_delayed > 0 ? "text-red-400 font-medium" : "text-slate-500"}>
                        {r.days_delayed > 0 ? `${r.days_delayed}d` : "On Time"}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-mono text-xs bg-red-400/10 text-red-400 px-2 py-0.5 rounded">
                        {r.risk_score.toFixed(3)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card p-0 overflow-hidden">
            <DataTable
              columns={columns as never}
              data={(data?.items ?? []) as never}
              loading={isLoading}
              rowKey={(s) => (s as Shipment).id}
              emptyMessage="No shipments found"
            />
          </div>
        )}
      </div>
    </div>
  );
}
