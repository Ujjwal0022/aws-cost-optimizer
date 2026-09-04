import React, { useEffect, useState } from "react";
import { Topbar } from "../components/ui/Topbar";
import { Loader } from "../components/ui/Loader";
import { ErrorBox } from "../components/ui/ErrorBox";
import {
  ComposedChart, Area, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface ForecastDay {
  date: string;
  predicted_cost: number;
  confidence_low: number;
  confidence_high: number;
}

interface ForecastData {
  forecast: ForecastDay[];
  next_30_days_total: number;
  current_mtd: number;
  last_month_total: number;
  daily_trend_actual: Array<{ date: string; amount: number }>;
  trend_direction: string;
  trend_emoji: string;
  slope_per_day: number;
  model_accuracy: { r2: number; rmse: number };
  confidence: "high" | "medium" | "low";
  days_of_data_used: number;
}

const CONFIDENCE_STYLE = {
  high:   { color: "#276749", bg: "#F0FFF4", border: "#9AE6B4", label: "High Confidence" },
  medium: { color: "#975A16", bg: "#FFFBEB", border: "#FAF089", label: "Medium Confidence" },
  low:    { color: "#C53030", bg: "#FFF5F5", border: "#FED7D7", label: "Low Confidence" },
};

export const Forecast: React.FC = () => {
  const [data, setData]       = useState<ForecastData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState("");

  const load = async () => {
    setLoading(true); setError("");
    try {
      const res = await fetch(`${BASE_URL}/api/forecast`);
      setData(await res.json());
    } catch (e: any) {
      setError(e.message || "Failed to generate forecast");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <Loader text="Generating 30-day cost forecast..." />;
  if (error)   return <ErrorBox message={error} />;
  if (!data)   return null;

  const conf = CONFIDENCE_STYLE[data.confidence];

  // Merge actual + forecast for chart
  const actualFormatted = data.daily_trend_actual.map(d => ({
    date:   d.date.slice(5),
    actual: d.amount,
    predicted: null,
    conf_low:  null,
    conf_high: null,
  }));

  const forecastFormatted = data.forecast.map(d => ({
    date:      d.date.slice(5),
    actual:    null,
    predicted: d.predicted_cost,
    conf_low:  d.confidence_low,
    conf_high: d.confidence_high,
  }));

  const chartData = [...actualFormatted, ...forecastFormatted];

  const momChange = data.last_month_total > 0
    ? ((data.next_30_days_total - data.last_month_total) / data.last_month_total) * 100
    : 0;

  return (
    <div>
      <Topbar
        title="Cost Forecast"
        subtitle="ML-powered 30-day cost prediction using linear regression"
        onRefresh={load}
        loading={loading}
      />

      {/* Summary cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20 }}>
        {[
          {
            label: "Next 30 Days",
            value: `$${data.next_30_days_total.toFixed(2)}`,
            sub: `${momChange > 0 ? "+" : ""}${momChange.toFixed(1)}% vs last month`,
            color: momChange > 20 ? "#C53030" : momChange > 0 ? "#975A16" : "#276749",
            bg: momChange > 20 ? "#FFF5F5" : momChange > 0 ? "#FFFBEB" : "#F0FFF4",
          },
          {
            label: "Current MTD",
            value: `$${data.current_mtd.toFixed(2)}`,
            sub: "This month so far",
            color: "#2B6CB0", bg: "#EBF8FF",
          },
          {
            label: "Last Month",
            value: `$${data.last_month_total.toFixed(2)}`,
            sub: "Total billed",
            color: "#276749", bg: "#F0FFF4",
          },
          {
            label: "Trend",
            value: `${data.trend_emoji} ${data.trend_direction}`,
            sub: `$${Math.abs(data.slope_per_day).toFixed(4)}/day`,
            color: "#475569", bg: "#f8fafc",
          },
        ].map((card) => (
          <div key={card.label} style={{ background: card.bg, borderRadius: 12, padding: 16, border: "0.5px solid #e2e8f0" }}>
            <div style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>{card.label}</div>
            <div style={{ fontSize: 18, fontWeight: 900, color: card.color }}>{card.value}</div>
            <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 3 }}>{card.sub}</div>
          </div>
        ))}
      </div>

      {/* Model info bar */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <div style={{ background: conf.bg, border: `0.5px solid ${conf.border}`, borderRadius: 10, padding: "8px 16px", display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 16 }}>🎯</span>
          <div>
            <div style={{ fontSize: 10, color: "#94a3b8" }}>Model Confidence</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: conf.color }}>{conf.label}</div>
          </div>
        </div>
        <div style={{ background: "#fff", border: "0.5px solid #e2e8f0", borderRadius: 10, padding: "8px 16px" }}>
          <div style={{ fontSize: 10, color: "#94a3b8" }}>R² Score</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#334155" }}>{data.model_accuracy.r2.toFixed(3)}</div>
        </div>
        <div style={{ background: "#fff", border: "0.5px solid #e2e8f0", borderRadius: 10, padding: "8px 16px" }}>
          <div style={{ fontSize: 10, color: "#94a3b8" }}>RMSE</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#334155" }}>${data.model_accuracy.rmse.toFixed(4)}</div>
        </div>
        <div style={{ background: "#fff", border: "0.5px solid #e2e8f0", borderRadius: 10, padding: "8px 16px" }}>
          <div style={{ fontSize: 10, color: "#94a3b8" }}>Training Data</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#334155" }}>{data.days_of_data_used} days</div>
        </div>
        <div style={{ background: "#EBF8FF", border: "0.5px solid #BEE3F8", borderRadius: 10, padding: "8px 16px" }}>
          <div style={{ fontSize: 10, color: "#94a3b8" }}>Algorithm</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#2B6CB0" }}>Linear Regression</div>
        </div>
      </div>

      {/* Main forecast chart */}
      <div style={{ background: "#fff", borderRadius: 12, padding: 20, border: "0.5px solid #f1f5f9", marginBottom: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "#64748b" }}>
            Actual Cost + 30-Day Forecast
          </h3>
          <div style={{ display: "flex", gap: 16, fontSize: 11, color: "#94a3b8" }}>
            <span><span style={{ display: "inline-block", width: 16, height: 3, background: "#2B6CB0", marginRight: 4, verticalAlign: "middle", borderRadius: 2 }} />Actual</span>
            <span><span style={{ display: "inline-block", width: 16, height: 3, background: "#E53E3E", marginRight: 4, verticalAlign: "middle", borderRadius: 2, borderTop: "2px dashed #E53E3E" }} />Forecast</span>
            <span><span style={{ display: "inline-block", width: 16, height: 8, background: "rgba(229,62,62,0.1)", marginRight: 4, verticalAlign: "middle", borderRadius: 2 }} />95% CI</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={260}>
          <ComposedChart data={chartData}>
            <defs>
              <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#2B6CB0" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#2B6CB0" stopOpacity={0}   />
              </linearGradient>
              <linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#E53E3E" stopOpacity={0.1} />
                <stop offset="95%" stopColor="#E53E3E" stopOpacity={0}   />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0F4F8" />
            <XAxis dataKey="date" tick={{ fontSize: 9 }} tickLine={false} axisLine={false} interval={7} />
            <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `$${v.toFixed(2)}`} />
            <Tooltip formatter={(v: any) => v !== null ? [`$${Number(v).toFixed(4)}`, ""] : ["-", ""]} />
            <Area type="monotone" dataKey="conf_high" fill="rgba(229,62,62,0.08)" stroke="none" />
            <Area type="monotone" dataKey="conf_low"  fill="#fff"                  stroke="none" />
            <Area type="monotone" dataKey="actual"    fill="url(#ag)" stroke="#2B6CB0" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="predicted" stroke="#E53E3E" strokeWidth={2} strokeDasharray="5 3" dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Forecast table - next 7 days */}
      <div style={{ background: "#fff", borderRadius: 12, border: "0.5px solid #f1f5f9", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
        <div style={{ padding: "14px 20px", borderBottom: "0.5px solid #f1f5f9" }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "#1e293b" }}>📅 Next 7 Days — Detailed Forecast</h3>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              {["Date", "Predicted Cost", "Low Estimate", "High Estimate"].map(h => (
                <th key={h} style={{ padding: "8px 16px", textAlign: "left", fontSize: 10, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.forecast.slice(0, 7).map((day, i) => (
              <tr key={i} style={{ borderTop: "0.5px solid #f8fafc" }}>
                <td style={{ padding: "10px 16px", color: "#334155", fontWeight: 500 }}>{day.date}</td>
                <td style={{ padding: "10px 16px", fontWeight: 700, color: "#2B6CB0" }}>${day.predicted_cost.toFixed(4)}</td>
                <td style={{ padding: "10px 16px", color: "#276749" }}>${day.confidence_low.toFixed(4)}</td>
                <td style={{ padding: "10px 16px", color: "#C53030" }}>${day.confidence_high.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p style={{ fontSize: 11, color: "#94a3b8", marginTop: 12, textAlign: "right" }}>
        * Forecast based on linear regression. CI = 95% confidence interval.
      </p>
    </div>
  );
};
