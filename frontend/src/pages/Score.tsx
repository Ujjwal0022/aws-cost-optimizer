import React, { useEffect, useState } from "react";
import { Topbar } from "../components/ui/Topbar";
import { Loader } from "../components/ui/Loader";
import { ErrorBox } from "../components/ui/ErrorBox";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Dimension {
  name: string; weight: number; icon: string;
  score: number; value: string; detail: string;
  status: "ok" | "warning" | "critical" | "unknown";
}

interface ScoreData {
  overall_score: number; label: string;
  color: string; bg: string; emoji: string;
  total_potential_savings: number;
  dimensions: Record<string, Dimension>;
  top_recommendations: Array<{ text: string; savings: number; severity: string; type: string }>;
  calculated_at: string;
}

const STATUS_COLOR = {
  ok:       { bar: "#48BB78", bg: "#F0FFF4", text: "#276749" },
  warning:  { bar: "#ECC94B", bg: "#FFFBEB", text: "#975A16" },
  critical: { bar: "#FC8181", bg: "#FFF5F5", text: "#C53030" },
  unknown:  { bar: "#94a3b8", bg: "#f8fafc", text: "#64748b" },
};

const ScoreRing: React.FC<{ score: number; color: string }> = ({ score, color }) => {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  return (
    <svg width="140" height="140" viewBox="0 0 140 140">
      <circle cx="70" cy="70" r={r} fill="none" stroke="#f1f5f9" strokeWidth="12" />
      <circle
        cx="70" cy="70" r={r} fill="none"
        stroke={color} strokeWidth="12"
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transform: "rotate(-90deg)", transformOrigin: "70px 70px", transition: "stroke-dashoffset 1s ease" }}
      />
      <text x="70" y="65" textAnchor="middle" style={{ fontSize: 28, fontWeight: 900, fill: color }}>{score}</text>
      <text x="70" y="82" textAnchor="middle" style={{ fontSize: 11, fill: "#94a3b8" }}>out of 100</text>
    </svg>
  );
};

export const Score: React.FC = () => {
  const [data, setData]       = useState<ScoreData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState("");

  const load = async () => {
    setLoading(true); setError("");
    try {
      const res = await fetch(`${BASE_URL}/api/score`);
      setData(await res.json());
    } catch (e: any) { setError(e.message || "Failed to load score"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <Loader text="Calculating your AWS optimization score..." />;
  if (error)   return <ErrorBox message={error} />;
  if (!data)   return null;

  const dims = Object.values(data.dimensions);

  return (
    <div>
      <Topbar title="Optimization Score" subtitle="How efficiently are you using AWS?" onRefresh={load} loading={loading} />

      {/* Hero score card */}
      <div style={{ background: "#fff", borderRadius: 16, padding: 28, marginBottom: 20, border: "0.5px solid #f1f5f9", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", display: "flex", alignItems: "center", gap: 32 }}>
        <ScoreRing score={data.overall_score} color={data.color} />
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{ fontSize: 28 }}>{data.emoji}</span>
            <span style={{ fontSize: 24, fontWeight: 900, color: data.color }}>{data.label}</span>
          </div>
          <p style={{ fontSize: 13, color: "#64748b", marginBottom: 14 }}>
            Your AWS account efficiency score based on EC2 utilization, storage waste, unused IPs, cost trend, and budget health.
          </p>
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ background: "#F0FFF4", border: "0.5px solid #9AE6B4", borderRadius: 10, padding: "8px 16px" }}>
              <div style={{ fontSize: 18, fontWeight: 900, color: "#276749" }}>${data.total_potential_savings.toFixed(2)}</div>
              <div style={{ fontSize: 10, color: "#68D391" }}>potential monthly savings</div>
            </div>
            <div style={{ background: "#EBF8FF", border: "0.5px solid #BEE3F8", borderRadius: 10, padding: "8px 16px" }}>
              <div style={{ fontSize: 18, fontWeight: 900, color: "#2B6CB0" }}>{dims.length}</div>
              <div style={{ fontSize: 10, color: "#63B3ED" }}>dimensions analyzed</div>
            </div>
          </div>
        </div>
      </div>

      {/* Dimension breakdown */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 20 }}>
        {dims.map((dim) => {
          const sc = STATUS_COLOR[dim.status] || STATUS_COLOR.unknown;
          return (
            <div key={dim.name} style={{ background: "#fff", borderRadius: 12, padding: 18, border: "0.5px solid #f1f5f9", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 20 }}>{dim.icon}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#1e293b" }}>{dim.name}</div>
                    <div style={{ fontSize: 10, color: "#94a3b8" }}>Weight: {dim.weight}%</div>
                  </div>
                </div>
                <div style={{ fontSize: 22, fontWeight: 900, color: sc.text }}>{dim.score}</div>
              </div>

              {/* Progress bar */}
              <div style={{ background: "#f1f5f9", borderRadius: 99, height: 8, marginBottom: 8 }}>
                <div style={{ width: `${dim.score}%`, height: 8, borderRadius: 99, background: sc.bar, transition: "width 1s ease" }} />
              </div>

              <div style={{ fontSize: 11, color: "#64748b", fontWeight: 500 }}>{dim.value}</div>
              <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 3 }}>{dim.detail}</div>
            </div>
          );
        })}
      </div>

      {/* Top recommendations */}
      {data.top_recommendations.length > 0 && (
        <div style={{ background: "#fff", borderRadius: 12, border: "0.5px solid #f1f5f9", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div style={{ padding: "14px 20px", borderBottom: "0.5px solid #f1f5f9" }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "#1e293b" }}>💡 Top Recommendations to Improve Score</h3>
          </div>
          {data.top_recommendations.map((rec, i) => (
            <div key={i} style={{ padding: "14px 20px", borderTop: i > 0 ? "0.5px solid #f8fafc" : "none", display: "flex", alignItems: "flex-start", gap: 12 }}>
              <span style={{ fontSize: 18, flexShrink: 0 }}>{{ EC2: "🖥️", EBS: "💾", EIP: "🌐", RDS: "🗄️" }[rec.type] || "☁️"}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: "#334155" }}>{rec.text}</div>
                <div style={{ fontSize: 11, color: "#276749", fontWeight: 600, marginTop: 4 }}>Save ${rec.savings.toFixed(2)}/month</div>
              </div>
              <span style={{ padding: "2px 8px", borderRadius: 99, fontSize: 10, fontWeight: 700, background: rec.severity === "HIGH" ? "#FED7D7" : rec.severity === "MEDIUM" ? "#FEFCBF" : "#C6F6D5", color: rec.severity === "HIGH" ? "#C53030" : rec.severity === "MEDIUM" ? "#975A16" : "#276749", flexShrink: 0 }}>
                {rec.severity}
              </span>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 12, fontSize: 11, color: "#94a3b8", textAlign: "right" }}>
        Last calculated: {new Date(data.calculated_at).toLocaleString()}
      </div>
    </div>
  );
};
