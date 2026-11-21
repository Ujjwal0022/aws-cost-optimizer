import { useState, useEffect } from "react";
import { useAccount } from "../context/AccountContext";
import { useAccountApi } from "../hooks/useAccountApi";
import NoAccountBanner from "../components/ui/NoAccountBanner";
import {
  Lightbulb, RefreshCw, Loader2, TrendingDown,
  Server, Database, HardDrive, Zap, DollarSign,
  AlertTriangle, CheckCircle, ChevronDown, ChevronUp,
  Filter, ArrowUpDown,
} from "lucide-react";

// ── Config ────────────────────────────────────────────────────────────────────
const CATEGORY_CONFIG = {
  RIGHTSIZING:        { label: "Rightsizing",         color: "blue",   icon: Server    },
  IDLE_RESOURCE:      { label: "Idle Resource",        color: "yellow", icon: Zap       },
  RESERVED_INSTANCE:  { label: "Reserved Instance",    color: "green",  icon: DollarSign},
};

const RISK_CONFIG = {
  LOW:    { color: "text-green-400  bg-green-400/10  border-green-400/30",  label: "Low Risk"    },
  MEDIUM: { color: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30", label: "Medium Risk" },
  HIGH:   { color: "text-red-400    bg-red-400/10    border-red-400/30",    label: "High Risk"   },
};

const TYPE_ICONS = {
  EC2:          <Server    className="w-4 h-4" />,
  EBS:          <HardDrive className="w-4 h-4" />,
  "Elastic IP": <Zap       className="w-4 h-4" />,
  RDS:          <Database  className="w-4 h-4" />,
  Lambda:       <Zap       className="w-4 h-4" />,
};

// ── Confidence Bar ────────────────────────────────────────────────────────────
function ConfidenceBar({ value }) {
  const color = value >= 90 ? "bg-green-500" : value >= 70 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-8">{value}%</span>
    </div>
  );
}

// ── Single Recommendation Card ────────────────────────────────────────────────
function RecommendationCard({ rec }) {
  const [expanded, setExpanded] = useState(false);
  const risk = RISK_CONFIG[rec.risk] || RISK_CONFIG.MEDIUM;
  const cat  = CATEGORY_CONFIG[rec.category] || { label: rec.category, color: "blue" };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="p-4 flex items-start gap-4">
        <div className="w-9 h-9 bg-blue-600/20 rounded-lg flex items-center justify-center shrink-0 text-blue-400">
          {TYPE_ICONS[rec.resource_type] || <Server className="w-4 h-4" />}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-white font-medium text-sm truncate">{rec.resource_name}</span>
            <span className="text-gray-500 text-xs font-mono">{rec.resource_id}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${risk.color}`}>
              {risk.label}
            </span>
          </div>
          <p className="text-gray-400 text-xs">{rec.issue}</p>

          {/* Action */}
          <div className="mt-2 flex items-start gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
            <p className="text-blue-300 text-xs">{rec.action}</p>
          </div>
        </div>

        {/* Savings */}
        <div className="text-right shrink-0">
          <p className="text-green-400 font-bold text-lg">${rec.monthly_saving}</p>
          <p className="text-gray-500 text-xs">/month</p>
          <p className="text-gray-400 text-xs mt-0.5">${rec.annual_saving}/yr</p>
        </div>
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 pb-3 flex items-center gap-2 text-gray-400 hover:text-white text-xs transition"
      >
        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        {expanded ? "Hide details" : "Show details"}
      </button>

      {/* Expanded Details */}
      {expanded && (
        <div className="px-4 pb-4 pt-2 border-t border-gray-700 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-700/50 rounded-lg p-3">
              <p className="text-gray-400 text-xs mb-1">Current Config</p>
              <p className="text-white text-sm font-mono">{rec.current_config}</p>
            </div>
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
              <p className="text-gray-400 text-xs mb-1">Recommended</p>
              <p className="text-green-300 text-sm font-mono">{rec.recommended_config}</p>
            </div>
          </div>

          <div>
            <p className="text-gray-400 text-xs mb-1.5">Confidence Score</p>
            <ConfidenceBar value={rec.confidence} />
          </div>

          {rec.details && Object.keys(rec.details).length > 0 && (
            <div className="bg-gray-700/30 rounded-lg p-3 text-xs space-y-1">
              {Object.entries(rec.details).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-gray-400 capitalize">{k.replace(/_/g, " ")}</span>
                  <span className="text-gray-200">{String(v)}</span>
                </div>
              ))}
            </div>
          )}

          <div className="text-xs text-gray-500">
            Resource Type: <span className="text-gray-300">{rec.resource_type}</span>
            &nbsp;·&nbsp;
            Category: <span className="text-gray-300">{cat.label}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function Recommendations() {
  const { selectedAccount }   = useAccount();
  const { get }               = useAccountApi();
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter]   = useState("ALL");
  const [sortBy, setSortBy]   = useState("saving"); // saving | confidence | risk

  const fetchData = async () => {
    if (!selectedAccount) return;
    setLoading(true);
    try {
      const res = await get("/recommendations/");
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [selectedAccount?.id]);

  if (!selectedAccount) return <NoAccountBanner />;

  // Filter + sort
  const categories = data
    ? ["ALL", ...Object.keys(data.by_category || {})]
    : ["ALL"];

  const filtered = (data?.recommendations || [])
    .filter(r => filter === "ALL" || r.category === filter)
    .sort((a, b) => {
      if (sortBy === "saving")     return b.monthly_saving - a.monthly_saving;
      if (sortBy === "confidence") return b.confidence - a.confidence;
      if (sortBy === "risk") {
        const order = { LOW: 0, MEDIUM: 1, HIGH: 2 };
        return order[a.risk] - order[b.risk];
      }
      return 0;
    });

  return (
    <div className="p-6 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Lightbulb className="w-6 h-6 text-yellow-400" /> Recommendations
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            AI-powered optimization recommendations for {selectedAccount.account_name}
          </p>
        </div>
        <button onClick={fetchData} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {loading && !data ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
              <p className="text-gray-400 text-sm">Total Recommendations</p>
              <p className="text-white text-3xl font-bold mt-1">{data?.total_count ?? "—"}</p>
            </div>
            <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
              <p className="text-green-400 text-sm">Monthly Savings</p>
              <p className="text-white text-3xl font-bold mt-1">${data?.monthly_savings ?? "—"}</p>
            </div>
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
              <p className="text-blue-400 text-sm">Annual Savings</p>
              <p className="text-white text-3xl font-bold mt-1">${data?.annual_savings ?? "—"}</p>
            </div>
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
              <p className="text-yellow-400 text-sm">Categories</p>
              <p className="text-white text-3xl font-bold mt-1">
                {Object.keys(data?.by_category || {}).length}
              </p>
            </div>
          </div>

          {/* Category Breakdown */}
          {data?.by_category && Object.keys(data.by_category).length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(data.by_category).map(([cat, recs]) => {
                const cfg     = CATEGORY_CONFIG[cat] || { label: cat, color: "blue" };
                const savings = recs.reduce((s, r) => s + r.monthly_saving, 0);
                return (
                  <div key={cat} className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex items-center gap-4">
                    <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center text-blue-400">
                      {cfg.icon ? <cfg.icon className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                    </div>
                    <div>
                      <p className="text-white font-medium">{cfg.label}</p>
                      <p className="text-gray-400 text-xs">{recs.length} items · ${savings.toFixed(2)}/mo savings</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Filters + Sort */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1.5">
              <Filter className="w-4 h-4 text-gray-400" />
              <span className="text-gray-400 text-sm">Filter:</span>
            </div>
            {categories.map(cat => (
              <button key={cat} onClick={() => setFilter(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  filter === cat
                    ? "bg-blue-600 text-white"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}>
                {cat === "ALL" ? "All" : (CATEGORY_CONFIG[cat]?.label || cat)}
                {cat !== "ALL" && ` (${data?.by_category?.[cat]?.length ?? 0})`}
              </button>
            ))}

            <div className="ml-auto flex items-center gap-1.5">
              <ArrowUpDown className="w-4 h-4 text-gray-400" />
              <select value={sortBy} onChange={e => setSortBy(e.target.value)}
                className="bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-1.5 text-xs">
                <option value="saving">Sort by Savings</option>
                <option value="confidence">Sort by Confidence</option>
                <option value="risk">Sort by Risk</option>
              </select>
            </div>
          </div>

          {/* Recommendation Cards */}
          <div className="space-y-3">
            {filtered.length === 0 ? (
              <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
                <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
                <p className="text-white font-semibold">No recommendations found</p>
                <p className="text-gray-400 text-sm mt-1">
                  {filter === "ALL"
                    ? "Your AWS account looks well-optimized!"
                    : `No ${CATEGORY_CONFIG[filter]?.label || filter} recommendations`}
                </p>
              </div>
            ) : (
              filtered.map(rec => <RecommendationCard key={rec.id} rec={rec} />)
            )}
          </div>

          {data?.generated_at && (
            <p className="text-gray-500 text-xs text-center">
              Last analyzed: {new Date(data.generated_at).toLocaleString()}
            </p>
          )}
        </>
      )}
    </div>
  );
}





