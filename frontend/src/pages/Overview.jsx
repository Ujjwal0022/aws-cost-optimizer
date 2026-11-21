import { useState, useEffect } from "react";
import { useAccount } from "../context/AccountContext";
import { useAccountApi } from "../hooks/useAccountApi";
import NoAccountBanner from "../components/ui/NoAccountBanner";
import {
  DollarSign, TrendingUp, TrendingDown, AlertTriangle,
  Server, Database, Loader2, RefreshCw, Cloud
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

function StatCard({ title, value, sub, icon: Icon, color = "blue", trend }) {
  const colors = {
    blue:   "text-blue-400  bg-blue-400/10",
    green:  "text-green-400 bg-green-400/10",
    red:    "text-red-400   bg-red-400/10",
    yellow: "text-yellow-400 bg-yellow-400/10",
    purple: "text-purple-400 bg-purple-400/10",
  };
  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-gray-400 text-sm">{title}</p>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${colors[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <p className="text-white text-2xl font-bold">{value}</p>
      {sub && <p className="text-gray-400 text-xs mt-1">{sub}</p>}
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-xs ${trend >= 0 ? "text-red-400" : "text-green-400"}`}>
          {trend >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {Math.abs(trend)}% vs last month
        </div>
      )}
    </div>
  );
}

export default function Overview() {
  const { selectedAccount } = useAccount();
  const { get }             = useAccountApi();
  const [costs, setCosts]   = useState(null);
  const [waste, setWaste]   = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    if (!selectedAccount) return;
    setLoading(true);
    try {
      const [costsData, wasteData] = await Promise.all([
        get("/resources/costs"),
        get("/resources/waste"),
      ]);
      setCosts(costsData);
      setWaste(wasteData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [selectedAccount?.id]);

  if (!selectedAccount) return <NoAccountBanner />;

  return (
    <div className="p-6 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Overview</h1>
          <p className="text-gray-400 text-sm mt-1 flex items-center gap-1.5">
            <Cloud className="w-4 h-4" />
            {selectedAccount.account_name} — {selectedAccount.aws_account_id}
          </p>
        </div>
        <button onClick={fetchData} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {loading && !costs ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
        </div>
      ) : (
        <>
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              title="Current Month Cost"
              value={`$${costs?.current_month_cost?.toFixed(2) ?? "—"}`}
              sub={`Projected: $${costs?.projected_month_end?.toFixed(2) ?? "—"}`}
              icon={DollarSign} color="blue"
              trend={costs?.month_over_month}
            />
            <StatCard
              title="Previous Month"
              value={`$${costs?.previous_month_cost?.toFixed(2) ?? "—"}`}
              sub="Last month total"
              icon={TrendingUp} color="purple"
            />
            <StatCard
              title="Waste Detected"
              value={waste?.total_waste_items ?? "—"}
              sub={`Save $${waste?.monthly_savings ?? 0}/mo`}
              icon={AlertTriangle} color="yellow"
            />
            <StatCard
              title="Daily Average"
              value={`$${costs?.daily_avg?.toFixed(2) ?? "—"}`}
              sub="Current month avg"
              icon={Server} color="green"
            />
          </div>

          {/* Cost Chart */}
          {costs?.daily_costs?.length > 0 && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
              <h2 className="text-white font-semibold mb-4">Daily Cost — Current Month</h2>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={costs.daily_costs}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" tick={{ fill: "#9CA3AF", fontSize: 10 }}
                    tickFormatter={v => v.slice(5)} />
                  <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }}
                    tickFormatter={v => `$${v}`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151" }}
                    formatter={v => [`$${Number(v).toFixed(2)}`, "Cost"]} />
                  <Line type="monotone" dataKey="cost" stroke="#3B82F6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top Services + Waste */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* Top Services */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
              <h2 className="text-white font-semibold mb-4">Top Services by Cost</h2>
              <div className="space-y-3">
                {costs?.top_services?.slice(0, 6).map((svc, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-300 truncate">{svc.service}</span>
                        <span className="text-white font-medium ml-2">${svc.cost}</span>
                      </div>
                      <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${svc.pct}%` }} />
                      </div>
                    </div>
                    <span className="text-gray-400 text-xs w-10 text-right">{svc.pct}%</span>
                  </div>
                ))}
                {(!costs?.top_services || costs.top_services.length === 0) && (
                  <p className="text-gray-400 text-sm">No cost data available</p>
                )}
              </div>
            </div>

            {/* Waste Summary */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
              <h2 className="text-white font-semibold mb-4">Waste Summary</h2>
              {waste ? (
                <div className="space-y-3">
                  {Object.entries(waste.breakdown || {}).map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                      <div>
                        <p className="text-white text-sm font-medium capitalize">
                          {key.replace(/_/g, " ")}
                        </p>
                        <p className="text-gray-400 text-xs">{val.count} items</p>
                      </div>
                      {val.savings > 0 && (
                        <span className="text-green-400 text-sm font-bold">
                          ${val.savings}/mo
                        </span>
                      )}
                    </div>
                  ))}
                  <div className="border-t border-gray-700 pt-3 flex justify-between">
                    <span className="text-gray-300 font-medium">Total Savings</span>
                    <span className="text-green-400 font-bold">${waste.monthly_savings}/mo</span>
                  </div>
                </div>
              ) : (
                <p className="text-gray-400 text-sm">No waste data available</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}





