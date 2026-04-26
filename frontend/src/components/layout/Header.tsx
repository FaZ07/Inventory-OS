"use client";

import { Search, RefreshCw } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) router.push(`/inventory?search=${encodeURIComponent(query)}`);
  };

  return (
    <header className="h-16 border-b border-surface-border bg-surface/80 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-20">
      <div>
        <h2 className="font-semibold text-white">{title}</h2>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>

      <form onSubmit={handleSearch} className="flex items-center gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search SKU or product…"
            className="pl-9 pr-4 py-2 bg-surface border border-surface-border rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 w-64"
          />
        </div>
        <button type="button" className="p-2 rounded-lg bg-surface-hover hover:bg-slate-600 transition-colors" title="Refresh">
          <RefreshCw className="w-4 h-4 text-slate-400" />
        </button>
      </form>
    </header>
  );
}
