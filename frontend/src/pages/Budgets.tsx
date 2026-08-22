import React, { useEffect, useState } from "react";
import { getBudgetAlerts } from "../lib/api";
import { BudgetAlert } from "../types";
import { Topbar }   from "../components/ui/Topbar";
import { Loader }   from "../components/ui/Loader";
import { ErrorBox } from "../components/ui/ErrorBox";
import { CheckCircle, AlertTriangle, XCircle } from "lucide-react";

const STATUS_ICON = { OK: CheckCircle, WARNING: AlertTriangle, EXCEEDED: XCircle };

export const Budgets: React.FC = () => {
  const [data,    setData]    = useState<BudgetAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

  const load = async () => {
    setLoading(true); setError("");
    try { setData(await getBudgetAlerts()); }
    catch (e: any) { setError(e?.response?.data?.detail || e.message || "Failed"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  if (loading) return <Loader text="Checking AWS Budgets..." />;

  return (
    <div>
      <Topbar title="Budget Alerts" subtitle="AWS Budgets spend vs limit" onRefresh={load} loading={loading} />
      {error && <ErrorBox message={error} />}
      {!error && data.length === 0 && (
        <div className="info-box">
          <p className="info-box-title">No budgets configured</p>
          <p className="info-box-sub">Set up AWS Budgets in your account and add your Account ID in the backend .env to see alerts here.</p>
        </div>
      )}
      <div className="budget-grid">
        {data.map((b) => {
          const Icon = STATUS_ICON[b.status];
          const pct  = Math.min(b.alert_threshold_percent, 100);
          return (
            <div key={b.budget_name} className={`budget-card budget-${b.status}`}>
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 12 }}>
                <div>
                  <p className="budget-name">{b.budget_name}</p>
                  <p className="budget-limit">Limit: <strong>${b.budget_limit.toFixed(2)}</strong></p>
                </div>
                <div className={`status-chip status-${b.status}`}>
                  <Icon size={12} /> {b.status}
                </div>
              </div>
              <div className="budget-bar-wrap">
                <div className="budget-bar-labels">
                  <span>Spent: ${b.actual_spend.toFixed(2)}</span>
                  <span>{b.alert_threshold_percent.toFixed(1)}%</span>
                </div>
                <div className="budget-bar-bg">
                  <div className={`budget-bar-fill bar-${b.status}`} style={{ width: `${pct}%` }} />
                </div>
              </div>
              <p className="budget-forecast">Forecasted: <span>${b.forecasted_spend.toFixed(2)}</span></p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
