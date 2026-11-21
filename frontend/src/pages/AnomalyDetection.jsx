import { useContext, useEffect, useState } from "react";
import { AccountContext } from "../context/AccountContext";
const API = import.meta.env.VITE_API_URL;
export default function AnomalyDetection() {
  const { activeAccount, getAuthHeader } = useContext(AccountContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  useEffect(() => { if (activeAccount) fetchData(); }, [activeAccount]);
  async function fetchData() {
    setLoading(true); setError(null);
    try {
      const headers = await getAuthHeader();
      const res = await fetch(`${API}/costs/anomalies?account_id=${activeAccount.aws_account_id}`, { headers });
      if (!res.ok) throw new Error("Failed to fetch anomalies");
      setData(await res.json());
    } catch(e) { setError(e.message); } finally { setLoading(false); }
  }
  if (!activeAccount) return <div className="p-8 text-gray-400">Select an AWS account first.</div>;
  if (loading) return <div className="p-8 text-gray-400">Scanning for anomalies...</div>;
  if (error) return <div className="p-8 text-red-400">Error: {error}</div>;
  const anomalies = data?.anomalies ?? [];
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">⚠️ Anomaly Detection</h1>
        <p className="text-gray-400 text-sm mt-1">AWS Cost Anomaly Detection · Last 30 days</p>
      </div>
      {anomalies.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <p className="text-4xl mb-3">✅</p>
          <p className="text-gray-300 font-semibold">No anomalies detected</p>
          <p className="text-gray-500 text-sm mt-1">Your spending looks normal for the last 30 days.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {anomalies.map(a => (
            <div key={a.id} className="bg-gray-900 border border-yellow-500/30 border-l-4 border-l-yellow-500 rounded-xl p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-white">{a.service}</span>
                <span className="text-yellow-400 font-bold text-lg">${a.impact} impact</span>
              </div>
              <div className="flex gap-6 text-sm text-gray-400">
                <span>📍 {a.region}</span>
                <span>📅 {a.start} → {a.end}</span>
                <span>🎯 Score: {a.score}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}





