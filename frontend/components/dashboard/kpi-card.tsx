"use client";

import { useEffect, useState } from "react";
import { cn, formatCurrency, formatNumber } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: number;
  format?: "number" | "currency" | "percent";
  icon: LucideIcon;
  trend?: string;
  className?: string;
}

export function KPICard({ title, value, format = "number", icon: Icon, trend, className }: KPICardProps) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const duration = 800;
    const steps = 30;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setDisplay(value);
        clearInterval(timer);
      } else {
        setDisplay(current);
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [value]);

  const formatted =
    format === "currency"
      ? formatCurrency(display)
      : format === "percent"
        ? `${display.toFixed(1)}%`
        : formatNumber(Math.round(display));

  return (
    <div className={cn("glass-card kpi-glow rounded-lg p-5 animate-slide-up", className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-2 text-2xl font-bold tracking-tight">{formatted}</p>
          {trend && <p className="mt-1 text-xs text-muted-foreground">{trend}</p>}
        </div>
        <div className="rounded-lg bg-primary/10 p-2.5">
          <Icon className="h-5 w-5 text-primary" />
        </div>
      </div>
    </div>
  );
}
