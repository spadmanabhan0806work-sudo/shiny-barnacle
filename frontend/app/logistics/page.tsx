"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, MapPin, Truck } from "lucide-react";
import { UtilizationBarChart } from "@/components/charts/chart-components";
import { PageShell } from "@/components/layout/page-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, type LogisticsAlert, type Shipment, type Vehicle, type Warehouse } from "@/lib/api";

export default function LogisticsPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [alerts, setAlerts] = useState<LogisticsAlert[]>([]);

  useEffect(() => {
    Promise.all([api.getShipments(), api.getWarehouses(), api.getVehicles(), api.getAlerts()]).then(
      ([s, w, v, a]) => {
        setShipments(s);
        setWarehouses(w);
        setVehicles(v);
        setAlerts(a);
      }
    );
  }, []);

  const statusBadge = (status: string) => {
    if (status === "delayed") return "danger";
    if (status === "at_risk") return "warning";
    if (status === "delivered") return "success";
    return "secondary";
  };

  const delayedCount = shipments.filter((s) => s.status === "delayed").length;

  return (
    <PageShell title="Logistics Dashboard" description="Shipment tracking, warehouse capacity, and fleet status">
      <div className="space-y-6">
        {delayedCount > 0 && (
          <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-3 sm:px-4 sm:py-3">
            <AlertTriangle className="h-5 w-5 text-red-400 shrink-0" />
            <p className="text-xs sm:text-sm">
              <span className="font-semibold text-red-400">{delayedCount} delayed shipments</span> require immediate attention
            </p>
          </div>
        )}

        <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg">Shipment Tracking</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tracking #</TableHead>
                      <TableHead>Supplier</TableHead>
                      <TableHead>Route</TableHead>
                      <TableHead>ETA</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {shipments.map((s) => (
                      <TableRow key={s.id}>
                        <TableCell className="font-mono text-xs whitespace-nowrap">{s.tracking_number}</TableCell>
                        <TableCell className="whitespace-nowrap">{s.supplier_name}</TableCell>
                        <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                          {s.origin} → {s.destination}
                        </TableCell>
                        <TableCell className="whitespace-nowrap">{s.eta || "TBD"}</TableCell>
                        <TableCell>
                          <Badge variant={statusBadge(s.status)}>{s.status.replace("_", " ")}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                <AlertTriangle className="h-4 w-4 text-amber-400" />
                Risk Alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 max-h-[350px] sm:max-h-[400px] overflow-y-auto">
              {alerts.map((a) => (
                <div key={a.id} className="rounded-lg border border-border/50 bg-muted/20 p-3 text-xs sm:text-sm">
                  <div className="flex items-center gap-2">
                    <Badge variant={a.severity === "high" ? "danger" : "warning"}>{a.severity}</Badge>
                  </div>
                  <p className="mt-1 font-medium">{a.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{a.description}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <UtilizationBarChart data={warehouses.map((w) => ({ name: w.name, utilization: w.utilization_pct }))} />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
              <Truck className="h-5 w-5 text-primary" />
              Fleet Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {vehicles.map((v) => (
                <div key={v.id} className="rounded-lg border border-border/50 bg-muted/20 p-4">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-semibold text-sm sm:text-base">{v.vehicle_id}</span>
                    <Badge variant={statusBadge(v.status)}>{v.status.replace("_", " ")}</Badge>
                  </div>
                  <p className="mt-2 text-xs sm:text-sm text-muted-foreground">{v.type}</p>
                  <div className="mt-3 flex items-center gap-1 text-xs text-muted-foreground">
                    <MapPin className="h-3 w-3 shrink-0" />
                    {v.location}
                  </div>
                  <p className="mt-1 text-xs">Driver: {v.driver}</p>
                  <p className="mt-1 text-xs">
                    Load: {v.current_load_tons}/{v.capacity_tons} tons
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}

