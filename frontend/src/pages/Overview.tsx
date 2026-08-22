import React, { useEffect, useState } from "react";
import { getCostSummary, getRecommendations } from "../lib/api";
import { CostSummary, ResourceSummary } from "../types";
import { StatCard }       from "../components/ui/StatCard";
import { Topbar }         from "../components/ui/Topbar";
import { Loader }         from "../components/ui/Loader";
import { ErrorBox }       from "../components/ui/ErrorBox";
import { DailyTrendChart }  from "../components/charts/DailyTrendChart";
import { TopServicesChart } from "../components/charts/TopServicesChart";
import { DollarSign, TrendingDown, TrendingUp, AlertTriangle } from "lucide-react";

export const Overview: React.FC = () => {
  const [cost,      setCost]      = useState<CostSummary | null>(null);
  const [resources, setResources] = useState<ResourceSummary | null>(null);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState("");

  const load = async () => {
    setLoading(true); setError("");
    try {
      const [c, r] = await Promise.all([getCostSummary(), getRecommendations()]);
      setCost(c); setResources(r);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Failed to load data");
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <Loader text="Fetching AWS cost data..." />;
  if (error)   return <ErrorBox message={error} />;
  if (!cost || !resources) return null;

  return (
    <div>
      <Topbar title="Cost Overview" subtitle="Month-to-date spend across your AWS account" onRefresh={load} loading={loading} />

      <div className="savings-hero">
        <div>
          <p className="savings-hero-label">Potential Monthly Savings</p>
          <p className="savings-hero-amount">
            ${resources.total_estimated_savings.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </p>
          <p className="savings-hero-sub">
            {resources.recommendations.length} waste items detected across your account
          </p>
        </div>
        <div className="savings-hero-icon">
          <DollarSign size={36} />
        </div>
      </div>

      <div className="stat-grid">
        <StatCard title="MTD Spend"  value={`$${cost.total_cost_mtd.toFixed(2)}`}           subtitle="This month so far"       icon={<DollarSign size={20}/>}    color="blue"   />
        <StatCard title="Last Month" value={`$${cost.total_cost_last_month.toFixed(2)}`}     subtitle="Total billed"            icon={<TrendingDown size={20}/>}  color="green"  />
        <StatCard title="Forecast"   value={`$${cost.forecast_end_of_month.toFixed(2)}`}     subtitle="Projected end of month"  icon={<TrendingUp size={20}/>}    color="yellow" />
        <StatCard title="Waste Items" value={`${resources.recommendations.length}`}
          subtitle={`${resources.recommendations.filter(r=>r.severity==="HIGH").length} HIGH severity`}
          icon={<AlertTriangle size={20}/>} color="red" />
      </div>

      <div className="chart-grid">
        <DailyTrendChart data={cost.daily_trend} />
        <TopServicesChart data={cost.top_services} />
      </div>
    </div>
  );
};
