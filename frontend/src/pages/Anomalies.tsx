import React, { useEffect, useState } from "react";
import { Topbar } from "../components/ui/Topbar";
import { Loader } from "../components/ui/Loader";
import { ErrorBox } from "../components/ui/ErrorBox";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Anomaly {
  index: number; date: string; amount: number;
  mean_cost: number; deviation_pct: number;
  severity: "HIGH" | "MEDIUM" | "LOW";
  type: "spike" | "drop";
  explanation: string;
}

interface AnomalyData {
  anomalies_found: number;
  anomalies: Anomaly[];
  daily_trend: Array<{ date: string; amount: number }>;
  mean_daily_cost: number;
  total_days_analyzed: number;
  algorithm: string;
}

const SEV = {
  HIGH:   { bg: "#FFF5F5", border: "#FED7D7", text: "#C53030", badge: "#FED7D7" },
  MEDIUM: { bg: "#FFFBEB", border: "#FAF089", text: "#975A16", badge: "#FEFCBF" },
  LOW:    { bg: "#F0FFF4", border: "#9AE6B4", text: "#276749", badge: "#C6F6D5" },
};

const CustomDot = (props: any) => {
  const { cx, cy, payload, anomalyDates } = props;
  if (anomalyDates.includes(payload.date)) {
    return <circle cx={cx} cy={cy} r={6} fill="#E53E3E" stroke="#fff" strokeWidth={2} />;
  }
  return null;
};

export const Anomalies: React.FC = () => {
  const [data, setData]       = useState<AnomalyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);

  const load = async () => {
    setLoading(true); setError("");
    try {
      const res = await fetch(`${BASE_URL}/api/anomalies`);
      setData(await res.json());
    } catch (e: any) { setError(e.message || "Failed to detect anomalies"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <Loader text="Running anomaly detection on your cost data..." />;
  if (error)   return <ErrorBox message={error} />;
  if (!data)   return null;

  const anomalyDates = data.anomalies.map(a => a.date);
  const chartData    = data.daily_trend.map(d => ({
    date:   d.date.slice(5),
    amount: d.amount,
    full_date: d.date,
  }));

  return (
    <div>
      <Topbar title="AI Anomaly Detection" subtitle="ML-powered cost spike and drop detection" onRefresh={load} loading={loading} />

      {/* Summary pills */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <div style={{ background: "#fff", border: "0.5px solid #e2e8f0", borderRadius: 12, padding: "12px 20px", display: "flex", alignItems: "center", gap: 10, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <span style={{ fontSize: 24 }}>🤖</span>
          <div>
            <div style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>Algorithm</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#2B6CB0" }}>{data.algorithm}</div>
          </div>
        </div>
        <div style={{ background: data.anomalies_found > 0 ? "#FFF5F5" : "#F0FFF4", border: `0.5px solid ${data.anomalies_found > 0 ? "#FED7D7" : "#9AE6B4"}`, borderRadius: 12, padding: "12px 20px", display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 24 }}>{data.anomalies_found > 0 ? "🚨" : "✅"}</span>
          <div>
            <div style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>Anomalies Found</div>
            <div style={{ fontSize: 20, fontWeight: 900, color: data.anomalies_found > 0 ? "#C53030" : "#276749" }}>{data.anomalies_found}</div>
          </div>
        </div>
        <div style={{ background: "#fff", border: "0.5px solid #e2e8f0", borderRadius: 12, padding: "12px 20px" }}>
          <div style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>Avg Daily Cost</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#334155" }}>${data.mean_daily_cost.toFixed(4)}</div>
        </div>
        <div style={{ background: "#fff", border: "0.5px solid #e2e8f0", borderRadius: 12, padding: "12px 20px" }}>
          <div style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>Days Analyzed</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#334155" }}>{data.total_days_analyzed}</div>
        </div>
      </div>

      {/* Chart with anomaly markers */}
      <div style={{ background: "#fff", borderRadius: 12, padding: 20, border: "0.5px solid #f1f5f9", marginBottom: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "#64748b" }}>Daily Cost Trend — Anomalies Highlighted</h3>
          <div style={{ display: "flex", alignItems: "center", gap: 16, fontSize: 11, color: "#94a3b8" }}>
            <span><span style={{ display: "inline-block", width: 12, height: 3, background: "#2B6CB0", borderRadius: 2, marginRight: 4, verticalAlign: "middle" }} />Normal</span>
            <span><span style={{ display: "inline-block", width: 10, height: 10, background: "#E53E3E", borderRadius: "50%", marginRight: 4, verticalAlign: "middle" }} />Anomaly</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2B6CB0" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#2B6CB0" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0F4F8" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} interval={4} />
            <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `$${v.toFixed(2)}`} />
            <Tooltip formatter={(v: number) => [`$${v.toFixed(4)}`, "Cost"]} />
            {data.mean_daily_cost > 0 && (
              <ReferenceLine y={data.mean_daily_cost} stroke="#94a3b8" strokeDasharray="4 4" label={{ value: "avg", position: "right", fontSize: 10, fill: "#94a3b8" }} />
            )}
            <Area type="monotone" dataKey="amount" stroke="#2B6CB0" strokeWidth={2} fill="url(#ag)"
              dot={(props: any) => <CustomDot {...props} anomalyDates={anomalyDates} />}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Anomaly list */}
      {data.anomalies_found === 0 ? (
        <div style={{ background: "#F0FFF4", border: "0.5px solid #9AE6B4", borderRadius: 12, padding: 28, textAlign: "center" }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: "#276749" }}>No anomalies detected!</div>
          <div style={{ fontSize: 12, color: "#68D391", marginTop: 4 }}>Your daily cost is consistent over the last {data.total_days_analyzed} days.</div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "#1e293b" }}>🚨 Detected Anomalies</h3>
          {data.anomalies.map((a, i) => {
            const s = SEV[a.severity];
            return (
              <div key={i} style={{ background: s.bg, border: `0.5px solid ${s.border}`, borderRadius: 12, overflow: "hidden" }}>
                <div style={{ padding: "14px 18px", display: "flex", alignItems: "center", gap: 14, cursor: "pointer" }} onClick={() => setExpanded(expanded === i ? null : i)}>
                  <span style={{ fontSize: 24 }}>{a.type === "spike" ? "📈" : "📉"}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: s.text }}>{a.date}</span>
                      <span style={{ padding: "1px 8px", borderRadius: 99, fontSize: 10, fontWeight: 700, background: s.badge, color: s.text }}>{a.severity}</span>
                      <span style={{ padding: "1px 8px", borderRadius: 99, fontSize: 10, fontWeight: 600, background: "rgba(0,0,0,0.06)", color: "#64748b", textTransform: "capitalize" }}>{a.type}</span>
                    </div>
                    <div style={{ fontSize: 12, color: "#64748b" }}>
                      Cost: <strong style={{ color: s.text }}>${a.amount.toFixed(4)}</strong>
                      {" "}({a.deviation_pct > 0 ? "+" : ""}{a.deviation_pct.toFixed(1)}% vs avg ${a.mean_cost.toFixed(4)})
                    </div>
                  </div>
                  <span style={{ fontSize: 16, color: "#94a3b8" }}>{expanded === i ? "▲" : "▼"}</span>
                </div>
                {expanded === i && (
                  <div style={{ padding: "12px 18px 16px", borderTop: `0.5px solid ${s.border}` }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: s.text, marginBottom: 6 }}>🤖 AI Explanation</div>
                    <div style={{ fontSize: 13, color: "#334155", lineHeight: 1.6, background: "rgba(255,255,255,0.6)", borderRadius: 8, padding: "10px 14px" }}>
                      {a.explanation}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
