"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { useAuthStore, saveTokens } from "@/lib/auth";
import toast from "react-hot-toast";
import { Zap, Mail, Lock } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useAuthStore();
  const [email, setEmail] = useState("admin@inventoryos.com");
  const [password, setPassword] = useState("admin123456");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data: tokens } = await authApi.login(email, password);
      saveTokens(tokens.access_token, tokens.refresh_token);
      const { data: user } = await authApi.me();
      setUser(user);
      toast.success(`Welcome back, ${user.full_name}!`);
      router.push("/dashboard");
    } catch {
      toast.error("Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">InventoryOS</h1>
            <p className="text-xs text-slate-500">Intelligent Supply Chain Platform</p>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">Sign in to your account</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Email address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  className="input pl-9" placeholder="you@company.com" required />
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  className="input pl-9" placeholder="••••••••" required />
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="btn-primary w-full justify-center flex items-center gap-2 py-2.5 disabled:opacity-60">
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="mt-4 p-3 bg-surface rounded-lg border border-surface-border">
            <p className="text-xs text-slate-400 mb-1">Demo credentials:</p>
            <code className="text-xs text-slate-300">admin@inventoryos.com / admin123456</code>
          </div>
        </div>
      </div>
    </div>
  );
}
