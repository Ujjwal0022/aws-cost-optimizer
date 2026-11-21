import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import {
  ClipboardList, RefreshCw, Loader2, CheckCircle,
  XCircle, Eye, Filter, Calendar, DollarSign,
  Server, HardDrive, Zap, Database,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const STATUS_CONFIG = {
  success:  { color: "text-green-400 bg-green-400/10 border-green-400/30",  icon: CheckCircle, label: "Success"  },
  failed:   { color: "text-red-400   bg-red-400/10   border-red-400/30",    icon: XCircle,     label: "Failed"   },
  dry_run:  { color: "text-blue-400  bg-blue-400/10  border-blue-400/30",   icon: Eye,         label: "Dry Run"  },
  pending:  { color: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30", icon: Loader2,   label: "Pending"  },
};

const TYPE_ICONS = {
  EC2:         <Server    className="w-4 h-4 text-blue-400" />,
  EBS:         <HardDrive className="w-4 h-4 text-yellow-400" />,
  "Elastic IP":<Zap       className="w-4 h-4 text-purple-400" />,
  RDS:         <Database  className="w-4 h-4 text-green-400" />,
};

export default function AuditLogs() {
  const { authFetch }     = useAuth();
  const [logs, setLogs]   = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const [filters, setFilters] = useState({
    status: "", action: "", resource_type: "", days: 30,
  });

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.status)        params.set("status",        filters.status);
      if (filters.action)        params.set("action",        filters.action);
      if (filters.resource_type) params.set("resource_type", filters.resource_type);
      params.set("days",  filters.days);
      params.set("limit", 50);

      const [logsRes, statsRes] = await Promise.all([
        authFetch(`/audit/?${params.toString()}`),
        authFetch("/audit/stats"),
      ]);
      const logsData  = await logsRes.json();
      const statsData = await statsRes.json();
      setLogs(logsData.logs  || []);
      setTotal(logsData.total || 0);
      setStats(statsData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLogs(); }, [filters]);

  const setFilter = (key, val) => setFilters(prev => ({ ...prev, [key]: val }));

  return (
    <div className="p-6 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ClipboardList className="w-6 h-6 text-blue-400" /> Audit Logs
          </h1>
          <p className="text-gray-400 mt-1 text-sm">Complete history of all remediation actions</p>
        </div>
        <button onClick={fetchLogs} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
            <p className="text-gray-400 text-sm">Total Actions</p>
            <p className="text-white text-2xl font-bold mt-1">{stats.total_actions}</p>
          </div>
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
            <p className="text-green-400 text-sm">Total Savings</p>
            <p className="text-white text-2xl font-bold mt-1">${stats.total_savings}/mo</p>
          </div>
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
            <p className="text-blue-400 text-sm">Successful</p>
            <p className="text-white text-2xl font-bold mt-1">{stats.by_status?.success || 0}</p>
          </div>
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
            <p className="text-yellow-400 text-sm">Dry Runs</p>
            <p className="text-white text-2xl font-bold mt-1">{stats.by_status?.dry_run || 0}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-gray-300 text-sm font-medium">Filters</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <select value={filters.status} onChange={e => setFilter("status", e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm">
            <option value="">All Statuses</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="dry_run">Dry Run</option>
          </select>

          <select value={filters.action} onChange={e => setFilter("action", e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm">
            <option value="">All Actions</option>
            <option value="STOP_EC2">Stop EC2</option>
            <option value="DELETE_EBS">Delete EBS</option>
            <option value="RELEASE_EIP">Release EIP</option>
            <option value="STOP_RDS">Stop RDS</option>
          </select>

          <select value={filters.resource_type} onChange={e => setFilter("resource_type", e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm">
            <option value="">All Resources</option>
            <option value="EC2">EC2</option>
            <option value="EBS">EBS</option>
            <option value="ELASTIC IP">Elastic IP</option>
            <option value="RDS">RDS</option>
          </select>

          <select value={filters.days} onChange={e => setFilter("days", Number(e.target.value))}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm">
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-700 flex justify-between items-center">
          <p className="text-white text-sm font-medium">
            {total} log{total !== 1 ? "s" : ""} found
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-7 h-7 animate-spin text-blue-400" />
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-16">
            <ClipboardList className="w-10 h-10 text-gray-600 mx-auto mb-3" />
            <p className="text-white font-medium">No audit logs yet</p>
            <p className="text-gray-400 text-sm mt-1">Actions taken via the Remediation Engine will appear here</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-left">
                  <th className="px-4 py-3 text-gray-400 font-medium">Action</th>
                  <th className="px-4 py-3 text-gray-400 font-medium">Resource</th>
                  <th className="px-4 py-3 text-gray-400 font-medium">Account</th>
                  <th className="px-4 py-3 text-gray-400 font-medium">Status</th>
                  <th className="px-4 py-3 text-gray-400 font-medium">Savings</th>
                  <th className="px-4 py-3 text-gray-400 font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(log => {
                  const status = STATUS_CONFIG[log.status] || STATUS_CONFIG.pending;
                  const StatusIcon = status.icon;
                  return (
                    <tr key={log.id} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition">
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs bg-gray-700 px-2 py-1 rounded text-white">
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {TYPE_ICONS[log.resource_type] || <Server className="w-4 h-4 text-gray-400" />}
                          <div>
                            <p className="text-white text-xs font-mono">{log.resource_id}</p>
                            <p className="text-gray-400 text-xs">{log.resource_type}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-300 text-xs">{log.account_name}</td>
                      <td className="px-4 py-3">
                        <span className={`flex items-center gap-1.5 w-fit text-xs px-2 py-1 rounded-full border ${status.color}`}>
                          <StatusIcon className="w-3 h-3" />
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {log.estimated_saving > 0 ? (
                          <span className="text-green-400 font-medium">${log.estimated_saving}/mo</span>
                        ) : (
                          <span className="text-gray-500">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}





