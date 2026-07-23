"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

const tooltipStyle = {
  contentStyle: { background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" },
  labelStyle: { color: "#94a3b8" },
};

export function ForecastAreaChart({ data }: { data: { period: string; actual?: number; forecast: number }[] }) {
  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle>Inventory Forecast</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="period" stroke="#64748b" fontSize={11} />
            <YAxis stroke="#64748b" fontSize={11} />
            <Tooltip {...tooltipStyle} />
            <Legend />
            <Area type="monotone" dataKey="actual" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} name="Actual" />
            <Area type="monotone" dataKey="forecast" stroke="#10b981" fill="#10b981" fillOpacity={0.15} name="Forecast" strokeDasharray="5 5" />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function UtilizationBarChart({ data }: { data: { name: string; utilization: number }[] }) {
  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle>Warehouse Utilization</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis type="number" domain={[0, 100]} stroke="#64748b" fontSize={11} />
            <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={120} />
            <Tooltip {...tooltipStyle} formatter={(v: number) => [`${v}%`, "Utilization"]} />
            <Bar dataKey="utilization" fill="#3b82f6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function TransportPieChart({ data }: { data: { status: string; count: number }[] }) {
  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle>Transportation Status</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={data} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={90} label>
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip {...tooltipStyle} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function DemandForecastChart({
  data,
}: {
  data: { period: string; actual: number | null; forecast: number; lower_bound: number; upper_bound: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="period" stroke="#64748b" fontSize={11} />
        <YAxis stroke="#64748b" fontSize={11} />
        <Tooltip {...tooltipStyle} />
        <Legend />
        <Line type="monotone" dataKey="actual" stroke="#3b82f6" strokeWidth={2} dot={false} name="Actual" />
        <Line type="monotone" dataKey="forecast" stroke="#10b981" strokeWidth={2} dot={false} name="Forecast" />
        <Line type="monotone" dataKey="upper_bound" stroke="#64748b" strokeDasharray="3 3" dot={false} name="Upper" />
        <Line type="monotone" dataKey="lower_bound" stroke="#64748b" strokeDasharray="3 3" dot={false} name="Lower" />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function RiskDistributionChart({ data }: { data: { name: string; value: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={70}>
          <Cell fill="#ef4444" />
          <Cell fill="#f59e0b" />
          <Cell fill="#10b981" />
        </Pie>
        <Tooltip {...tooltipStyle} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
