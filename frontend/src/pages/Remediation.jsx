import { useState, useEffect } from "react";
import { useAccount } from "../context/AccountContext";
import { useAccountApi } from "../hooks/useAccountApi";
import { useAuth } from "../context/AuthContext";
import NoAccountBanner from "../components/ui/NoAccountBanner";
import {
  Wrench, RefreshCw, Loader2, AlertTriangle,
  Shield, CheckCircle, XCircle, Play, Eye,
  HardDrive, Zap, Server, Database, Info,
} from "lucide-react";

const ACTION_META = {
  STOP_EC2:   { label: "Stop EC2",         icon: Server,    endpoint: "/remediation/stop-ec2",    field: "instance_id",    destructive: false },
  DELETE_EBS: { label: "Delete EBS",       icon: HardDrive, endpoint: "/remediation/delete-ebs",  field: "volume_id",      destructive: true  },
  RELEASE_EIP:{ label: "Release EIP",      icon: Zap,       endpoint: "/remediation/release-eip", field: "allocation_id",  destructive: true  },
  STOP_RDS:   { label: "Stop RDS",         icon: Database,  endpoint: "/remediation/stop-rds",    field: "db_instance_id", destructive: false },
};

// ── Confirmation Modal ────────────────────────────────────────────────────────
function ConfirmModal({ action, resourceId, resourceType, saving, onConfirm, onCancel, loading }) {
  const meta = ACTION_META[action] || {};
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 border border-gray-700 rounded-2xl max-w-md w-full p-6 space-y-5">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
            meta.destructive ? "bg-red-500/20" : "bg-yellow-500/20"
          }`}>
            <AlertTriangle className={`w-5 h-5 ${meta.destructive ? "text-red-400" : "text-yellow-400"}`} />
          </div>
          <div>
            <h3 className="text-white font-bold">Confirm {meta.label}</h3>
            <p className="text-gray-400 text-sm">This action will be logged in the audit trail</p>
          </div>
        </div>

        <div className="bg-gray-700/50 rounded-xl p-4 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Action</span>
            <span className="text-white font-mono">{action}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Resource</span>
            <span className="text-white font-mono truncate max-w-40">{resourceId}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Type</span>
            <span className="text-white">{resourceType}</span>
          </div>
          {saving > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-400">Est. Savings</span>
              <span className="text-green-400 font-bold">${saving}/mo</span>
            </div>
          )}
        </div>

        {meta.destructive && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex gap-2 text-red-400 text-sm">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>This is a <strong>destructive action</strong>. A safety snapshot will be created before deletion.</span>
          </div>
        )}

        <div className="flex gap-3">
          <button onClick={onCancel} disabled={loading}
            className="flex-1 px-4 py-2.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition">
            Cancel
          </button>
          <button onClick={onConfirm} disabled={loading}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
              meta.destructive
                ? "bg-red-600 hover:bg-red-500 text-white"
                : "bg-blue-600 hover:bg-blue-500 text-white"
            }`}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {loading ? "Executing..." : "Confirm & Execute"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Action Result Card ────────────────────────────────────────────────────────
function ResultCard({ result, onDismiss }) {
  if (!result) return null;
  const success = result.success;
  const dryRun  = result.dry_run;

  return (
    <div className={`rounded-xl border p-4 flex items-start gap-3 ${
      dryRun   ? "bg-blue-500/10 border-blue-500/30" :
      success  ? "bg-green-500/10 border-green-500/30" :
                 "bg-red-500/10 border-red-500/30"
    }`}>
      {dryRun   ? <Eye className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" /> :
       success  ? <CheckCircle className="w-5 h-5 text-green-400 shrink-0 mt-0.5" /> :
                  <XCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />}
      <div className="flex-1">
        <p className={`font-medium text-sm ${dryRun ? "text-blue-300" : success ? "text-green-300" : "text-red-300"}`}>
          {dryRun ? "Dry Run Preview" : success ? "Action Successful" : "Action Failed"}
        </p>
        <p className="text-gray-400 text-xs mt-1">{result.message}</p>
        {result.snapshot_id && (
          <p className="text-gray-400 text-xs mt-1">Safety snapshot: <span className="font-mono text-gray-300">{result.snapshot_id}</span></p>
        )}
        {result.audit_log_id && (
          <p className="text-gray-500 text-xs mt-1">Audit Log ID: {result.audit_log_id}</p>
        )}
      </div>
      <button onClick={onDismiss} className="text-gray-500 hover:text-gray-300 text-xs">✕</button>
    </div>
  );
}

// ── Action Form ───────────────────────────────────────────────────────────────
function ActionForm({ actionKey, aws, onResult }) {
  const { authFetch }          = useAuth();
  const { selectedAccount }    = useAccount();
  const meta                   = ACTION_META[actionKey];
  const Icon                   = meta.icon;

  const [resourceId, setResourceId] = useState("");
  const [saving, setSaving]         = useState(0);
  const [dryRun, setDryRun]         = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading]       = useState(false);

  const execute = async (isDryRun) => {
    setLoading(true);
    try {
      const body = {
        [meta.field]:     resourceId,
        dry_run:          isDryRun,
        estimated_saving: saving,
        ...(actionKey === "DELETE_EBS" ? { create_snapshot: true } : {}),
      };

      const res  = await authFetch(
        `${meta.endpoint}?account_id=${selectedAccount.id}`,
        { method: "POST", body: JSON.stringify(body) },
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Action failed");
      onResult(data);
    } catch (err) {
      onResult({ success: false, dry_run: isDryRun, message: err.message });
    } finally {
      setLoading(false);
      setShowConfirm(false);
    }
  };

  return (
    <>
      {showConfirm && (
        <ConfirmModal
          action={actionKey}
          resourceId={resourceId}
          resourceType={meta.label}
          saving={saving}
          onConfirm={() => execute(false)}
          onCancel={() => setShowConfirm(false)}
          loading={loading}
        />
      )}

      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${
            meta.destructive ? "bg-red-500/20 text-red-400" : "bg-blue-500/20 text-blue-400"
          }`}>
            <Icon className="w-4 h-4" />
          </div>
          <div>
            <p className="text-white font-medium">{meta.label}</p>
            {meta.destructive && (
              <span className="text-xs text-red-400 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Destructive action
              </span>
            )}
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-gray-400 text-xs mb-1 block">Resource ID</label>
            <input
              type="text"
              value={resourceId}
              onChange={e => setResourceId(e.target.value)}
              placeholder={
                actionKey === "STOP_EC2"    ? "i-0abc1234567890" :
                actionKey === "DELETE_EBS"  ? "vol-0abc1234567890" :
                actionKey === "RELEASE_EIP" ? "eipalloc-0abc123" :
                "db-instance-identifier"
              }
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm font-mono placeholder-gray-500 focus:outline-none focus:border-blue-500 transition"
            />
          </div>
          <div>
            <label className="text-gray-400 text-xs mb-1 block">Estimated Monthly Saving ($)</label>
            <input
              type="number" min="0" step="0.01"
              value={saving}
              onChange={e => setSaving(parseFloat(e.target.value) || 0)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 transition"
            />
          </div>
        </div>

        <div className="flex gap-2">
          {/* Dry Run */}
          <button
            onClick={() => execute(true)}
            disabled={loading || !resourceId}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 text-white rounded-lg text-sm transition"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
            Dry Run
          </button>

          {/* Execute */}
          <button
            onClick={() => setShowConfirm(true)}
            disabled={loading || !resourceId}
            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition disabled:opacity-40 ${
              meta.destructive
                ? "bg-red-600 hover:bg-red-500 text-white"
                : "bg-blue-600 hover:bg-blue-500 text-white"
            }`}
          >
            <Play className="w-4 h-4" /> Execute
          </button>
        </div>
      </div>
    </>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function Remediation() {
  const { selectedAccount } = useAccount();
  const [results, setResults] = useState([]);

  if (!selectedAccount) return <NoAccountBanner />;

  const addResult = (r) => setResults(prev => [r, ...prev]);
  const removeResult = (i) => setResults(prev => prev.filter((_, idx) => idx !== i));

  return (
    <div className="p-6 space-y-6">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Wrench className="w-6 h-6 text-blue-400" /> Remediation Engine
        </h1>
        <p className="text-gray-400 mt-1 text-sm">
          Apply optimizations with user approval — every action is logged in the audit trail
        </p>
      </div>

      {/* How it works */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 flex gap-3">
        <Shield className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-blue-300 font-medium text-sm">Safe by Design</p>
          <p className="text-gray-400 text-xs mt-1">
            Always use <strong className="text-white">Dry Run</strong> first to preview the action.
            Then click <strong className="text-white">Execute</strong> to confirm.
            All actions are logged in the Audit Trail with timestamps, user, and savings.
          </p>
        </div>
      </div>

      {/* Flow */}
      <div className="flex items-center gap-2 text-xs text-gray-400 flex-wrap">
        {["Detect Waste", "→", "Recommendation", "→", "Dry Run Preview", "→", "User Approval", "→", "Execute", "→", "Audit Log"].map((step, i) => (
          <span key={i} className={step === "→" ? "text-gray-600" : "bg-gray-700 px-2.5 py-1 rounded-full text-gray-300"}>
            {step}
          </span>
        ))}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-2">
          {results.map((r, i) => (
            <ResultCard key={i} result={r} onDismiss={() => removeResult(i)} />
          ))}
        </div>
      )}

      {/* Action Forms */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.keys(ACTION_META).map(actionKey => (
          <ActionForm
            key={actionKey}
            actionKey={actionKey}
            aws={selectedAccount}
            onResult={addResult}
          />
        ))}
      </div>

      {/* Info */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 flex gap-3">
        <Info className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
        <p className="text-gray-400 text-xs">
          Resource IDs can be found on the <strong className="text-white">Waste Detector</strong> or{" "}
          <strong className="text-white">Recommendations</strong> pages.
          All executions are permanently recorded in the <strong className="text-white">Audit Logs</strong>.
        </p>
      </div>
    </div>
  );
}





