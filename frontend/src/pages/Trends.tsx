import React, { useEffect, useState } from "react";
import { getCostSummary } from "../lib/api";
import { CostSummary } from "../types";
import { Topbar }           from "../components/ui/Topbar";
import { Loader }           from "../components/ui/Loader";
import { ErrorBox }         from "../components/ui/ErrorBox";
import { DailyTrendChart }  from "../components/charts/DailyTrendChart";
import { TopServicesChart } from "../components/charts/TopServicesChart";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

const COLORS = ["#2B6CB0","#3182CE","#4299E1","#63B3ED","#90CDF4","#BEE3F8","#93C5FD","#6EE7B7","#FCD34D","#FCA5A5"];

export const Trends: React.FC = () => {
  const [cost,    setCost]    = useState<CostSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

  const load = async () => {
    setLoading(true); setError("");
    try { setCost(await getCostSummary()); }
    catch (e: any) { setError(e?.response?.data?.detail || e.message || "Failed"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  if (loading) return <Loader text="Loading cost trends..." />;
  if (error)   return <ErrorBox message={error} />;
  if (!cost)   return null;

  const pieData = cost.top_services.slice(0, 7).map(s => ({
    name: s.service.replace("Amazon ", "").replace("AWS ", "").slice(0, 20),
    value: s.amount,
  }));
  const total = cost.top_services.reduce((a, s) => a + s.amount, 0);

  return (
    <div>
      <Topbar title="Cost Trends" subtitle="Daily spend and service breakdown" onRefresh={load} loading={loading} />
      <div style={{ marginBottom: 20 }}><DailyTrendChart data={cost.daily_trend} /></div>
      <div className="chart-grid" style={{ marginBottom: 20 }}>
        <TopServicesChart data={cost.top_services} />
        <div className="chart-card">
          <p className="chart-title">Service Cost Share (MTD)</p>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v: number) => [`$${v.toFixed(4)}`, "Cost"]} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="service-table-wrap">
        <div className="service-table-header">All Services — MTD Cost</div>
        <table className="data-table">
          <thead>
            <tr><th>Service</th><th style={{textAlign:"right"}}>Cost (USD)</th><th style={{textAlign:"right"}}>Share</th></tr>
          </thead>
          <tbody>
            {cost.top_services.map((svc) => {
              const pct = total ? (svc.amount / total) * 100 : 0;
              return (
                <tr key={svc.service}>
                  <td>{svc.service}</td>
                  <td style={{textAlign:"right", fontWeight:600}}>${svc.amount.toFixed(4)}</td>
                  <td style={{textAlign:"right"}}>
                    <div className="progress-bar-wrap">
                      <div className="progress-bar-bg">
                        <div className="progress-bar-fill" style={{ width: `${Math.min(pct, 100)}%` }} />
                      </div>
                      <span style={{ fontSize: 11, color: "#94a3b8", width: 40, textAlign: "right" }}>{pct.toFixed(1)}%</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
