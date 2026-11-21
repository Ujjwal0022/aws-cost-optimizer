import { useContext, useEffect, useState } from "react";
import { AccountContext } from "../context/AccountContext";

const API = import.meta.env.VITE_API_URL;

const REGIONS = [
  { value: "all",          label: "🌍 All Regions" },
  { value: "us-east-1",   label: "🇺🇸 US East (N. Virginia)" },
  { value: "us-west-2",   label: "🇺🇸 US West (Oregon)" },
  { value: "eu-west-1",   label: "🇪🇺 EU West (Ireland)" },
  { value: "eu-central-1",label: "🇩🇪 EU Central (Frankfurt)" },
  { value: "ap-south-1",  label: "🇮🇳 Asia Pacific (Mumbai)" },
  { value: "ap-southeast-1", label: "🇸🇬 Asia Pacific (Singapore)" },
  { value: "ap-northeast-1", label: "🇯🇵 Asia Pacific (Tokyo)" },
];

const toArr = (v, ...keys) => {
  if (Array.isArray(v)) return v;
  for (const k of [...keys, "data", "items", "results"]) {
    if (Array.isArray(v?.[k])) return v[k];
  }
  return [];
};

export default function MultiRegion() {
  const { activeAccount, getAuthHeader } = useContext(AccountContext);
  const [regionData, setRegionData] = useState([]);
  const [loading, setLoading]       = useState(false);
  const [selected, setSelected]     = useState("all");
  const [error, setError]           = useState(null);

  useEffect(() => { if (activeAccount) fetchData(); }, [activeAccount]);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const headers = await getAuthHeader();
      const res = await fetch(
        `${API}/costs/by-region?account_id=${activeAccount.aws_account_id}&period=30d`,
        { headers }
      );
      const json = await res.json();
      setRegionData(toArr(json, "regions", "data"));
    } catch (e) {
      console.error(e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (!activeAccount) return <div className="p-8 text-gray-400">Select an AWS account first.</div>;
  if (error)          return <div className="p-8 text-red-400">Error: {error}</div>;

  const filtered = selected === "all" ? regionData : regionData.filter(r => r.region === selected);
  const maxCost  = filtered.length ? Math.max(...filtered.map(r => r.cost), 1) : 1;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">🌍 Multi-Region</h1>
          <p className="text-gray-400 text-sm mt-1">{activeAccount.account_name} · Cost by region</p>
        </div>
        <select
          value={selected}
          onChange={e => setSelected(e.target.value)}
          className="bg-gray-900 border border-gray-700 text-white text-sm rounded-lg px-3 py-2"
        >
          {REGIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="text-gray-400">Loading region data...</div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left p-4 text-xs text-gray-500 uppercase tracking-wider">Region</th>
                <th className="text-left p-4 text-xs text-gray-500 uppercase tracking-wider">Cost (USD)</th>
                <th className="text-left p-4 text-xs text-gray-500 uppercase tracking-wider">Share</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={3} className="p-8 text-center text-gray-500">
                    No region data available — Cost Explorer data takes ~24h in new accounts.
                  </td>
                </tr>
              ) : (
                filtered.map(r => (
                  <tr key={r.region} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="p-4 text-white font-medium">{r.region}</td>
                    <td className="p-4 text-white">${r.cost.toFixed(2)}</td>
                    <td className="p-4 w-48">
                      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full"
                          style={{ width: `${(r.cost / maxCost) * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}