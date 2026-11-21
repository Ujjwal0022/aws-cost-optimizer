import { useContext, useEffect, useState } from "react";
import { AccountContext } from "../context/AccountContext";

const API = import.meta.env.VITE_API_URL;

const statusStyle = {
  ALARM:   "text-red-400 border-red-400/30 bg-red-400/10",
  WARNING: "text-yellow-400 border-yellow-400/30 bg-yellow-400/10",
  OK:      "text-green-400 border-green-400/30 bg-green-400/10",
};

export default function Alerts() {
  const { activeAccount, getAuthHeader } = useContext(AccountContext);
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  useEffect(() => { if (activeAccount) fetchBudgets(); }, [activeAccount]);

  async function fetchBudgets() {
    setLoading(true);
    setError(null);
    try {
      const headers = await getAuthHeader();
      const res  = await fetch(`${API}/api/costs/budgets?account_id=${activeAccount.aws_account_id}`, { headers });
      const data = await res.json();
      // backend array ya {budgets:[]} dono handle
      setBudgets(Array.isArray(data) ? data : (data?.budgets ?? []));
    } catch (e) {
      console.error(e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (!activeAccount) return <div className="p-8 text-gray-400">Select an AWS account first.</div>;
  if (loading)        return <div className="p-8 text-gray-400">Loading budget alerts...</div>;
  if (error)          return <div className="p-8 text-red-400">Error: {error}</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">🔔 Budget Alerts</h1>
        <p className="text-gray-400 text-sm mt-1">{activeAccount.account_name} · AWS Budgets</p>
      </div>

      {budgets.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <p className="text-4xl mb-3">💰</p>
          <p className="text-gray-300 font-semibold">No budgets configured</p>
          <p className="text-gray-500 text-sm mt-1">Create budgets in AWS Console → Billing → Budgets</p>
        </div>
      ) : (
        <div className="space-y-4">
          {budgets.map(b => (
            <div key={b.name ?? b.budget_name} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-white">{b.name ?? b.budget_name}</h3>
                <span className={`text-xs font-bold px-2 py-0.5 rounded border ${statusStyle[b.status] ?? statusStyle.OK}`}>
                  {b.status}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm mb-3">
                <div><p className="text-gray-500 text-xs">Limit</p><p className="font-bold text-white">${b.limit ?? b.budget_limit}</p></div>
                <div><p className="text-gray-500 text-xs">Actual</p><p className="font-bold text-white">${b.actual_spend}</p></div>
                <div><p className="text-gray-500 text-xs">Forecast</p><p className="font-bold text-white">${b.forecasted_spend ?? b.forecast_spend}</p></div>
              </div>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${(b.percent_used ?? b.alert_threshold_percent) >= 100 ? "bg-red-500" : (b.percent_used ?? b.alert_threshold_percent) >= 80 ? "bg-yellow-500" : "bg-green-500"}`}
                  style={{ width: `${Math.min(b.percent_used ?? b.alert_threshold_percent ?? 0, 100)}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{b.percent_used ?? b.alert_threshold_percent ?? 0}% used</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}