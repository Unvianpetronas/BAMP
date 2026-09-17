import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "BAMP — Battery-Aware Mission Planner",
};

const NAV = [
  ["/", "Dashboard"],
  ["/drones", "Drones"],
  ["/missions", "Mission Builder"],
  ["/simulation", "Simulation"],
  ["/comparison", "Comparison"],
  ["/scenarios", "Scenarios"],
  ["/models", "Models"],
  ["/training", "Custom Training"],
] as const;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <nav className="flex flex-wrap gap-4 border-b bg-white px-6 py-3 text-sm">
          {NAV.map(([href, label]) => (
            <Link key={href} href={href} className="hover:underline">
              {label}
            </Link>
          ))}
        </nav>
        <main className="px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
