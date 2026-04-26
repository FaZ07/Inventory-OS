"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Filter, Zap } from "lucide-react";
import toast from "react-hot-toast";
import { productsApi } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/Badge";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type { Product, PaginatedResponse, ProductSearchResult } from "@/types";

export default function InventoryPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [searchQ, setSearchQ] = useState("");
  const [fuzzy, setFuzzy] = useState(false);
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery<PaginatedResponse<Product>>({
    queryKey: ["products", page, category, status],
    queryFn: () => productsApi.list({ page, page_size: 20, category: category || undefined, status: status || undefined }).then((r) => r.data),
    enabled: !searchQ,
  });

  const { data: searchResults, isFetching: searching } = useQuery<ProductSearchResult[]>({
    queryKey: ["products-search", searchQ, fuzzy],
    queryFn: () => productsApi.search(searchQ, fuzzy, 20).then((r) => r.data),
    enabled: !!searchQ && searchQ.length >= 1,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => productsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["products"] });
      toast.success("Product deactivated");
    },
  });

  const products: Product[] = searchQ ? [] : (data?.items ?? []);

  const columns = [
    {
      key: "sku",
      header: "SKU",
      render: (p: Product) => <span className="font-mono text-brand-400 text-xs">{p.sku}</span>,
    },
    { key: "name", header: "Name", render: (p: Product) => <span className="font-medium text-white">{p.name}</span> },
    { key: "category", header: "Category", render: (p: Product) => <StatusBadge status={p.category} /> },
    {
      key: "total_quantity",
      header: "Stock",
      render: (p: Product) => (
        <span className={p.total_quantity <= p.min_stock_level ? "text-red-400 font-medium" : "text-slate-300"}>
          {formatNumber(p.total_quantity)}
        </span>
      ),
    },
    { key: "unit_price", header: "Price", render: (p: Product) => <span className="text-emerald-400">{formatCurrency(p.unit_price)}</span> },
    { key: "turnover_rate", header: "Turnover", render: (p: Product) => <span>{p.turnover_rate.toFixed(2)}x</span> },
    { key: "status", header: "Status", render: (p: Product) => <StatusBadge status={p.status} /> },
    {
      key: "actions",
      header: "",
      render: (p: Product) => (
        <button onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(p.id); }}
          className="text-xs text-red-400 hover:text-red-300 transition-colors">
          Remove
        </button>
      ),
    },
  ];

  return (
    <div className="animate-fade-in">
      <Header title="Inventory" subtitle="Product catalog & stock management" />

      <div className="p-6 space-y-4">

        {/* Toolbar */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                placeholder="Search SKU or product name…"
                className="input pl-9"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
              <input type="checkbox" checked={fuzzy} onChange={(e) => setFuzzy(e.target.checked)} className="accent-brand-500" />
              <Zap className="w-3.5 h-3.5 text-yellow-400" />
              Fuzzy (Trie)
            </label>
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="input w-40">
              <option value="">All Categories</option>
              {["electronics", "clothing", "food", "machinery", "chemicals", "furniture", "medical", "other"]
                .map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="input w-36">
              <option value="">All Statuses</option>
              {["active", "discontinued", "pending", "out_of_stock"].map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Product
          </button>
        </div>

        {/* Search Results (Trie) */}
        {searchQ && (
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-yellow-400" />
              <h3 className="font-medium text-white text-sm">
                {fuzzy ? "Fuzzy (Edit-Distance)" : "Prefix"} Search Results
                {searching && <span className="text-slate-500 text-xs ml-2">Searching…</span>}
              </h3>
              <span className="text-xs text-slate-500">— Trie-backed O(k)</span>
            </div>
            {(searchResults ?? []).length === 0 && !searching ? (
              <p className="text-slate-500 text-sm">No results for "{searchQ}"</p>
            ) : (
              <div className="space-y-2">
                {(searchResults ?? []).map((r) => (
                  <div key={r.product_id} className="flex items-center justify-between p-3 bg-surface rounded-lg border border-surface-border">
                    <div>
                      <span className="font-mono text-brand-400 text-xs mr-3">{r.sku}</span>
                      <span className="text-slate-300 text-sm">{r.name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      {r.edit_distance !== undefined && (
                        <span className="text-xs text-yellow-400">dist={r.edit_distance}</span>
                      )}
                      <span className="text-xs text-slate-500">score={r.score.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Products Table */}
        {!searchQ && (
          <div className="card p-0 overflow-hidden">
            <DataTable
              columns={columns as never}
              data={products as never}
              loading={isLoading}
              rowKey={(p) => (p as Product).id}
              emptyMessage="No products found"
            />
            {/* Pagination */}
            {data && data.total_pages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-surface-border">
                <p className="text-xs text-slate-500">
                  Showing {((page - 1) * 20) + 1}–{Math.min(page * 20, data.total)} of {formatNumber(data.total)}
                </p>
                <div className="flex items-center gap-2">
                  <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                    className="btn-secondary text-xs px-3 py-1.5 disabled:opacity-40">
                    Prev
                  </button>
                  <span className="text-xs text-slate-400">{page} / {data.total_pages}</span>
                  <button onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))} disabled={page === data.total_pages}
                    className="btn-secondary text-xs px-3 py-1.5 disabled:opacity-40">
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
