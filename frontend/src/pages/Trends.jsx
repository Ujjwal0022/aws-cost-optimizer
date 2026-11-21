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

export default function Trends() {
  const { activeAccount, getAuthHeader } = useContext(AccountContext);
  const [trend, setTrend]       = useState([]);
  const [services, setServices] = useState([]);
  const [period, setPeriod]     = useState("30d");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);

  useEffect(() => { if (activeAccount) fetchData(); }, [activeAccount, period]);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const headers = await getAuthHeader();
      const acct    = activeAccount.aws_account_id;
      const [tr, svc] = await Promise.all([
        fetch(`${API}/costs/trend?account_id=${acct}&period=${period}`, { headers }).then(r => r.json()),
        fetch(`${API}/costs/by-service?account_id=${acct}&period=${period}`, { headers }).then(r => r.json()),
      ]);
      setTrend(toArr(tr, "trends", "trend"));
      setServices(toArr(svc, "services", "by_service").slice(0, 8));
    } catch (e) {
      console.error(e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (!activeAccount) return <div className="p-8 text-gray-400">Select an AWS account first.</div>;
  if (error)          return <div className="p-8 text-red-400">Error: {error}</div>;

  const maxCost = trend.length    ? Math.max(...trend.map(d => d.cost), 1)    : 1;
  const maxSvc  = services.length ? Math.max(...services.map(s => s.cost), 1) : 1;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">📈 Cost Trends</h1>
          <p className="text-gray-400 text-sm mt-1">{activeAccount.account_name}</p>
        </div>
        <div className="flex gap-2">
          {["7d", "30d", "90d", "mtd"].map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                period === p ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"
              }`}
            >
              {p.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-gray-400">Loading...</div>
      ) : (
        <>
          {/* Daily Spend Chart */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">Daily Spend</h2>
            {trend.length === 0 ? (
              <p className="text-gray-500 text-sm">
                No data yet — AWS Cost Explorer data takes ~24h to appear in new accounts.
              </p>
            ) : (
              <div className="flex items-end gap-1 h-40">
                {trend.map(d => (
                  <div
                    key={d.date}
                    className="flex-1 flex flex-col items-center justify-end gap-1 h-full group relative"
                  >
                    <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-gray-700 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap pointer-events-none z-10">
                      {d.date.slice(5)}: ${d.cost}
                    </div>
                    <div
                      className="w-full bg-indigo-500 rounded-t hover:bg-indigo-400 transition-colors"
                      style={{ height: `${(d.cost / maxCost) * 100}%` }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top Services */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">Top Services</h2>
            {services.length === 0 ? (
              <p className="text-gray-500 text-sm">No service data available yet.</p>
            ) : (
              <div className="space-y-3">
                {services.map(s => (
                  <div key={s.service} className="flex items-center gap-3">
                    <span className="text-sm text-gray-300 w-48 truncate">{s.service}</span>
                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-500 rounded-full"
                        style={{ width: `${(s.cost / maxSvc) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-white w-20 text-right">
                      ${s.cost.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}