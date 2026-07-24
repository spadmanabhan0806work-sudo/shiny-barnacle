"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bot,
  FileText,
  LayoutDashboard,
  Package,
  Sparkles,
  Truck,
  Users,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Executive Dashboard", icon: LayoutDashboard },
  { href: "/forecast", label: "Demand Forecast", icon: BarChart3 },
  { href: "/suppliers", label: "Supplier Risk", icon: Users },
  { href: "/copilot", label: "Procurement Copilot", icon: Bot },
  { href: "/logistics", label: "Logistics", icon: Truck },
  { href: "/documents", label: "Document AI", icon: FileText },
  { href: "/reports", label: "Executive Report", icon: Sparkles },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={onMobileClose}
        />
      )}

      {/* Sidebar Drawer */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-screen w-64 flex-col border-r border-border bg-card/95 lg:bg-card/50 backdrop-blur-xl transition-transform duration-300 ease-in-out lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-border px-6">
          <div className="flex items-center gap-2">
            <Package className="h-7 w-7 text-primary" />
            <div>
              <h1 className="text-lg font-bold tracking-tight">Operyx AI</h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Supply Chain</p>
            </div>
          </div>
          <button
            onClick={onMobileClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground lg:hidden"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex-1 space-y-1 p-4 overflow-y-auto">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onMobileClose}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                  active
                    ? "bg-primary/15 text-primary border border-primary/20"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-border p-4">
          <div className="rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground">
            <p className="font-medium text-foreground">PoC Demo Mode</p>
            <p className="mt-1">AI Provider: Mock</p>
          </div>
        </div>
      </aside>
    </>
  );
}

