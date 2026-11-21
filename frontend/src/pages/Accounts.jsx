import { useState } from "react";
import { useAccount } from "../context/AccountContext";
import ConnectAccount from "./ConnectAccount";
import {
  Cloud,
  Plus,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Trash2,
  TestTube,
  RefreshCw,
  Shield,
  Globe,
} from "lucide-react";

const statusConfig = {
  connected: {
    color: "text-green-400",
    bg: "bg-green-400/10 border-green-400/30",
    icon: CheckCircle,
    label: "Connected",
  },
  failed: {
    color: "text-red-400",
    bg: "bg-red-400/10 border-red-400/30",
    icon: XCircle,
    label: "Failed",
  },
  pending: {
    color: "text-yellow-400",
    bg: "bg-yellow-400/10 border-yellow-400/30",
    icon: Clock,
    label: "Pending",
  },
  disconnected: {
    color: "text-gray-400",
    bg: "bg-gray-400/10 border-gray-400/30",
    icon: XCircle,
    label: "Disconnected",
  },
};

export default function Accounts() {
  const {
    accounts = [],
    loading,
    fetchAccounts,
    disconnectAccount,
    testConnection,
    selectAccount,
    selectedAccount,
  } = useAccount();

  const [showConnect, setShowConnect] = useState(false);
  const [testingId, setTestingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [testResults, setTestResults] = useState({});

  const handleTest = async (accountId) => {
    setTestingId(accountId);

    try {
      const result = await testConnection(accountId);

      setTestResults((prev) => ({
        ...prev,
        [accountId]: result,
      }));
    } catch (error) {
      setTestResults((prev) => ({
        ...prev,
        [accountId]: {
          valid: false,
          details: {
            error: error.message || "Connection test failed",
          },
        },
      }));
    } finally {
      setTestingId(null);
    }
  };

  const handleDisconnect = async (accountId) => {
    const confirmed = window.confirm(
      "Disconnect this AWS account? You can reconnect it anytime."
    );

    if (!confirmed) return;

    setDeletingId(accountId);

    try {
      await disconnectAccount(accountId);
    } catch (error) {
      console.error("Failed to disconnect account:", error);
    } finally {
      setDeletingId(null);
    }
  };

  const handleConnectSuccess = async () => {
    setShowConnect(false);

    try {
      await fetchAccounts();
    } catch (error) {
      console.error("Failed to refresh accounts:", error);
    }
  };

  if (showConnect) {
    return (
      <div className="p-6 flex items-center justify-center min-h-96">
        <ConnectAccount
          onSuccess={handleConnectSuccess}
          onCancel={() => setShowConnect(false)}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Cloud className="w-6 h-6 text-blue-400" />
            AWS Accounts
          </h1>

          <p className="text-gray-400 mt-1">
            Manage your connected AWS accounts
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={fetchAccounts}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>

          <button
            onClick={() => setShowConnect(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition font-medium"
          >
            <Plus className="w-4 h-4" />
            Connect Account
          </button>
        </div>
      </div>

      {/* Security Info */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 flex gap-3">
        <Shield className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />

        <div>
          <p className="text-blue-300 font-medium text-sm">
            Secure Cross-Account Access
          </p>

          <p className="text-gray-400 text-xs mt-1">
            We use AWS STS AssumeRole with ExternalId — no permanent
            credentials stored. Temporary credentials are generated per
            request and expire in 1 hour.
          </p>
        </div>
      </div>

      {/* Accounts List */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
        </div>
      ) : accounts.length === 0 ? (
        <div className="text-center py-16 space-y-4">
          <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto">
            <Cloud className="w-8 h-8 text-gray-600" />
          </div>

          <h3 className="text-white font-semibold text-lg">
            No AWS accounts connected
          </h3>

          <p className="text-gray-400 text-sm max-w-md mx-auto">
            Connect your first AWS account to start tracking costs and
            optimizing resources.
          </p>

          <button
            onClick={() => setShowConnect(true)}
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition"
          >
            <Plus className="w-4 h-4" />
            Connect your first account
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {accounts.map((account) => {
            const status =
              statusConfig[account.connection_status] ||
              statusConfig.pending;

            const StatusIcon = status.icon;
            const isSelected = selectedAccount?.id === account.id;
            const testResult = testResults[account.id];

            return (
              <div
                key={account.id}
                className={`bg-gray-800 rounded-xl border p-5 space-y-4 transition ${
                  isSelected ? "border-blue-500" : "border-gray-700"
                }`}
              >
                {/* Account Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-white font-semibold">
                        {account.account_name}
                      </h3>

                      {isSelected && (
                        <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                          Active
                        </span>
                      )}
                    </div>

                    <p className="text-gray-400 text-xs mt-0.5 font-mono">
                      {account.aws_account_id}
                    </p>
                  </div>

                  <span
                    className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${status.bg} ${status.color}`}
                  >
                    <StatusIcon className="w-3 h-3" />
                    {status.label}
                  </span>
                </div>

                {/* Details */}
                <div className="space-y-2 text-xs">
                  <div className="flex items-center gap-2 text-gray-400">
                    <Globe className="w-3.5 h-3.5" />
                    {account.default_region}
                  </div>

                  <div
                    className="text-gray-500 font-mono truncate"
                    title={account.role_arn}
                  >
                    {account.role_arn}
                  </div>

                  {account.last_synced_at && (
                    <div className="text-gray-500">
                      Last synced:{" "}
                      {new Date(account.last_synced_at).toLocaleString()}
                    </div>
                  )}
                </div>

                {/* Test Result */}
                {testResult && (
                  <div
                    className={`text-xs rounded-lg p-2.5 ${
                      testResult.valid
                        ? "bg-green-500/10 border border-green-500/20 text-green-400"
                        : "bg-red-500/10 border border-red-500/20 text-red-400"
                    }`}
                  >
                    {testResult.valid
                      ? `✅ Connection valid — Account: ${
                          testResult.details?.account_id || "Unknown"
                        }`
                      : `❌ ${
                          testResult.details?.error ||
                          "Connection test failed"
                        }`}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-1">
                  {!isSelected && (
                    <button
                      onClick={() => selectAccount(account)}
                      className="flex-1 bg-blue-600 hover:bg-blue-500 text-white text-xs py-2 rounded-lg transition font-medium"
                    >
                      Use This Account
                    </button>
                  )}

                  <button
                    onClick={() => handleTest(account.id)}
                    disabled={testingId === account.id}
                    className="flex items-center gap-1.5 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs rounded-lg transition disabled:opacity-50"
                  >
                    {testingId === account.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <TestTube className="w-3.5 h-3.5" />
                    )}

                    Test
                  </button>

                  <button
                    onClick={() => handleDisconnect(account.id)}
                    disabled={deletingId === account.id}
                    title="Disconnect account"
                    className="flex items-center gap-1.5 px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs rounded-lg transition border border-red-500/20 disabled:opacity-50"
                  >
                    {deletingId === account.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}