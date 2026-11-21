import { useContext, useEffect, useState } from "react";
import { AccountContext } from "../context/AccountContext";

const API = import.meta.env.VITE_API_URL;

const toArr = (v, ...keys) => {
  if (Array.isArray(v)) return v;
  for (const k of [...keys, "data", "items", "results"]) {
    if (Array.isArray(v?.[k])) return v[k];
  }
  return [];
};

export default function CostForecast() {
  const { activeAccount, getAuthHeader } = useContext(AccountContext);
  const [trend, setTrend]     = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  useEffect(() => { if (activeAccount) fetchData(); }, [activeAccount]);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const headers = await getAuthHeader();
      const acct = activeAccount.aws_account_id;
      const [tr, su] = await Promise.all([
        fetch(`${API}/costs/trend?account_id=${acct}&period=30d`, { headers }).then(r => r.json()),
        fetch(`${API}/costs/summary?account_id=${acct}&period=30d`, { headers }).then(r => r.json()),
      ]);
      setTrend(toArr(tr, "trends", "trend"));
      setSummary(Array.isArray(su) ? su[0] : su);
    } catch (e) {
      console.error(e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (!activeAccount) return <div className="p-8 text-gray-400">Select an AWS account first.</div>;
  if (loading)        return <div className="p-8 text-gray-400">Loading forecast...</div>;
  if (error)          return <div className="p-8 text-red-400">Error: {error}</div>;

  const maxCost = trend.length ? Math.max(...trend.map(d => d.cost), 1) : 1;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">🔮 Cost Forecast</h1>
        <p className="text-gray-400 text-sm mt-1">
          {activeAccount.account_name} · Last 30 days + month-end projection
        </p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-3 gap-4">
          {[
            ["MTD Spend",        `$${summary.total_cost ?? "0"}`],
            ["Month-End Forecast", summary.forecast ? `$${summary.forecast}` : "N/A"],
            ["Top Service",      summary.services?.[0]?.service ?? "—"],
          ].map(([label, val]) => (
            <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
              <p className="text-2xl font-bold text-white mt-1">{val}</p>
            </div>
          ))}
        </div>
      )}

      {/* Chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-gray-300 mb-4">Daily Spend — Last 30 Days</h2>
        {trend.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No data yet — AWS Cost Explorer data takes ~24h to appear in new accounts.
          </p>
        ) : (
          <div className="flex items-end gap-1 h-32">
            {trend.map(d => (
              <div key={d.date} className="flex-1 flex flex-col items-center justify-end gap-1 h-full">
                <div
                  className="w-full bg-indigo-500 rounded-t opacity-75 hover:opacity-100 transition-opacity"
                  style={{ height: `${(d.cost / maxCost) * 100}%` }}
                  title={`${d.date}: $${d.cost}`}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}