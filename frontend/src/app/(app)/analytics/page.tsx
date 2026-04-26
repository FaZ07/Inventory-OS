"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
} from "recharts";
import { analyticsApi } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { formatCurrency } from "@/lib/utils";
import { TrendingUp, Brain, Cpu } from "lucide-react";
import type { SupplierRank } from "@/types";

type ForecastResult = {
  product_id: number;
  periods_ahead: number;
  forecast: number[];
  trend: number;
  rmse: number;
  mape: number;
  confidence_lower: number[];
  confidence_upper: number[];
  error?: string;
};

const THEME = { grid: "#334155", text: "#94a3b8", blue: "#3b82f6", green: "#10b981", yellow: "#f59e0b", red: "#ef4444" };

function AlgoTag({ label, color = "blue" }: { label: string; color?: "blue" | "yellow" | "green" }) {
  const cls = { blue: "text-blue-400 bg-blue-400/10 border-blue-400/20", yellow: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20", green: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" };
  return <span className={`badge border text-xs ${cls[color]}`}>{label}</span>;
}

export default function AnalyticsPage() {
  const [productId, setProductId] = useState(1);
  const [periods, setPeriods] = useState(30);

  const { data: forecast, isLoading: fLoading } = useQuery<ForecastResult | undefined>({
    queryKey: ["forecast", productId, periods],
    queryFn: () => analyticsApi.forecast(productId, periods).then((r) => r.data),
  });

  const { data: rankings } = useQuery<SupplierRank[]>({
    queryKey: ["supplier-rankings"],
    queryFn: () => analyticsApi.supplierRankings().then((r) => r.data),
  });

  const { data: health } = useQuery({
    queryKey: ["supply-chain-health"],
    queryFn: () => analyticsApi.supplyChainHealth().then((r) => r.data),
  });

  const { data: topProducts } = useQuery({
    queryKey: ["top-products-10"],
    queryFn: () => analyticsApi.topProducts(10).then((r) => r.data),
  });

  const forecastChartData = (forecast?.forecast ?? []).map((val, i) => ({
    period: `D+${i + 1}`,
    forecast: val,
    lower: forecast?.confidence_lower?.[i] ?? 0,
    upper: forecast?.confidence_upper?.[i] ?? 0,
  }));

  const radarData = (rankings ?? []).slice(0, 5).map((s) => ({
    supplier: s.name.slice(0, 12),
    "On-Time": +(s.breakdown.on_time_delivery * 100).toFixed(1),
    Quality: +(s.breakdown.quality * 100).toFixed(1),
    Price: +(s.breakdown.price * 100).toFixed(1),
    "Lead Time": +(s.breakdown.lead_time * 100).toFixed(1),
  }));

  return (
    <div className="animate-fade-in">
      <Header title="Analytics" subtitle="Forecasting, ranking, and supply chain intelligence" />

      <div className="p-6 space-y-6">

        {/* Demand Forecast (Holt-Winters) */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Brain className="w-5 h-5 text-blue-400" />
              <div>
                <h3 className="font-semibold text-white">Demand Forecast</h3>
                <p className="text-xs text-slate-500">Holt-Winters Triple Exponential Smoothing</p>
              </div>
              <AlgoTag label="DP Smoothing" color="blue" />
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Product ID</label>
                <input type="number" value={productId} onChange={(e) => setProductId(+e.target.value)}
                  className="input w-20 py-1 text-xs" min={1} />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Periods</label>
                <select value={periods} onChange={(e) => setPeriods(+e.target.value)} className="input w-20 py-1 text-xs">
                  {[7, 14, 30, 60, 90].map((p) => <option key={p} value={p}>{p}d</option>)}
                </select>
              </div>
            </div>
          </div>

          {forecast && !forecast.error && (
            <div className="flex gap-4 mb-4">
              <div className="flex items-center gap-2 text-xs"><span className="text-slate-400">RMSE:</span><span className="text-white font-mono">{forecast.rmse}</span></div>
              <div className="flex items-center gap-2 text-xs"><span className="text-slate-400">MAPE:</span><span className="text-white font-mono">{forecast.mape}%</span></div>
              <div className="flex items-center gap-2 text-xs"><span className="text-slate-400">Trend:</span><span className={`font-mono ${forecast.trend >= 0 ? "text-emerald-400" : "text-red-400"}`}>{forecast.trend >= 0 ? "+" : ""}{forecast.trend}</span></div>
            </div>
          )}

          {fLoading ? (
            <div className="h-64 flex items-center justify-center text-slate-500">Loading forecast…</div>
          ) : forecast?.error ? (
            <div className="h-64 flex items-center justify-center text-yellow-400">Insufficient history (need ≥14 days)</div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={forecastChartData}>
                <defs>
                  <linearGradient id="ciGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={THEME.blue} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={THEME.blue} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={THEME.grid} />
                <XAxis dataKey="period" stroke={THEME.text} tick={{ fontSize: 11 }} interval={Math.floor(periods / 10)} />
                <YAxis stroke={THEME.text} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }} />
                <Area type="monotone" dataKey="upper" stroke="transparent" fill="url(#ciGrad)" name="Upper CI" />
                <Line type="monotone" dataKey="forecast" stroke={THEME.blue} strokeWidth={2} dot={false} name="Forecast" />
                <Line type="monotone" dataKey="lower" stroke={THEME.blue} strokeWidth={1} strokeDasharray="4 2" dot={false} name="Lower CI" opacity={0.4} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="grid grid-cols-2 gap-6">

          {/* Supplier Rankings (Merge Sort + Weighted Scoring) */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Cpu className="w-5 h-5 text-yellow-400" />
              <div>
                <h3 className="font-semibold text-white">Supplier Rankings</h3>
                <p className="text-xs text-slate-500">Multi-factor weighted scoring via Merge Sort</p>
              </div>
              <AlgoTag label="Merge Sort" color="yellow" />
            </div>
            <div className="space-y-3">
              {(rankings ?? []).slice(0, 8).map((s) => (
                <div key={s.supplier_id} className="flex items-center gap-3">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${s.rank === 1 ? "bg-yellow-400 text-yellow-900" : s.rank === 2 ? "bg-slate-400 text-slate-900" : s.rank === 3 ? "bg-amber-700 text-amber-100" : "bg-surface text-slate-400"}`}>
                    {s.rank}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-white">{s.name}</span>
                      <span className="text-xs text-slate-400">{(s.composite_score * 100).toFixed(1)}</span>
                    </div>
                    <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-brand-600 to-brand-400 rounded-full transition-all"
                        style={{ width: `${s.composite_score * 100}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Supplier Radar */}
          <div className="card">
            <h3 className="font-semibold text-white mb-2">Top 5 Supplier Performance Radar</h3>
            <p className="text-xs text-slate-500 mb-4">Normalized across all scoring dimensions</p>
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={radarData}>
                <PolarGrid stroke={THEME.grid} />
                <PolarAngleAxis dataKey="supplier" tick={{ fontSize: 11, fill: THEME.text }} />
                <Radar name="Score" dataKey="On-Time" stroke={THEME.blue} fill={THEME.blue} fillOpacity={0.2} />
                <Radar name="Quality" dataKey="Quality" stroke={THEME.green} fill={THEME.green} fillOpacity={0.2} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Products Bar Chart */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <h3 className="font-semibold text-white">Revenue by Product (Top 10)</h3>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={topProducts ?? []} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke={THEME.grid} horizontal={false} />
              <XAxis type="number" stroke={THEME.text} tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <YAxis type="category" dataKey="sku" width={90} tick={{ fontSize: 11 }} stroke={THEME.text} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                formatter={(v: number) => [formatCurrency(v), "Revenue"]} />
              <Bar dataKey="total_revenue" fill={THEME.green} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}
