"use client";

import { useState, type ReactNode } from "react";
import { Menu } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";

interface PageShellProps {
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
}

export function PageShell({ title, description, children, actions }: PageShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen">
      <Sidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />
      <main className="lg:pl-64 min-h-screen transition-all duration-300">
        <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur-xl">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between px-4 sm:px-6 lg:px-8 py-4 sm:py-5">
            <div className="flex items-start gap-3">
              <button
                onClick={() => setMobileOpen(true)}
                className="mt-0.5 rounded-lg border border-border p-2 text-muted-foreground hover:bg-accent hover:text-foreground lg:hidden shrink-0"
                aria-label="Open menu"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight">{title}</h1>
                {description && <p className="mt-1 text-xs sm:text-sm text-muted-foreground">{description}</p>}
              </div>
            </div>
            {actions && <div className="flex flex-wrap items-center gap-2 sm:gap-3">{actions}</div>}
          </div>
        </header>
        <div className="p-4 sm:p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}

