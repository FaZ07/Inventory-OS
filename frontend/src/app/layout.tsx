import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "InventoryOS — Intelligent Supply Chain Platform",
  description: "Enterprise-grade warehouse, logistics, and inventory management powered by advanced algorithms",
  keywords: ["inventory", "warehouse", "supply chain", "logistics", "enterprise"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-surface text-slate-200 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
