import { useState, useRef, useEffect } from "react";
import { useAccount } from "../../context/AccountContext";
import { useNavigate } from "react-router-dom";
import { ChevronDown, Cloud, Plus, CheckCircle, AlertCircle } from "lucide-react";

export default function AccountSelector() {
  const { accounts, selectedAccount, selectAccount, loading } = useAccount();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  if (loading) {
    return <div className="h-9 w-48 bg-gray-700 rounded-lg animate-pulse" />;
  }

  if (accounts.length === 0) {
    return (
      <button onClick={() => navigate("/accounts")}
        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition">
        <Plus className="w-4 h-4" /> Connect AWS Account
      </button>
    );
  }

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 border border-gray-700 hover:border-gray-600 text-white rounded-lg text-sm transition min-w-48">
        <span className="flex-1 text-left truncate">
          {selectedAccount?.account_name || "Select Account"}
        </span>
        {selectedAccount && (
          <span className={`w-2 h-2 rounded-full shrink-0 ${selectedAccount.connection_status === "connected" ? "bg-green-400" : "bg-red-400"
            }`} />
        )}
        <ChevronDown className={`w-4 h-4 text-gray-400 shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute top-full mt-1 left-0 w-64 bg-gray-800 border border-gray-700 rounded-xl shadow-xl z-50 overflow-hidden">
          <div className="p-2 space-y-0.5">
            {accounts.map((account) => (
              <button key={account.id}
                onClick={() => { selectAccount(account); setOpen(false); }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition text-left ${selectedAccount?.id === account.id
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                  }`}>
                <Cloud className="w-4 h-4 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{account.account_name}</p>
                  <p className="text-xs opacity-70 font-mono">{account.aws_account_id}</p>
                </div>
                {account.connection_status === "connected"
                  ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                  : <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />}
              </button>
            ))}
          </div>
          <div className="border-t border-gray-700 p-2">
            <button onClick={() => { navigate("/accounts"); setOpen(false); }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-blue-400 hover:bg-gray-700 rounded-lg transition">
              <Plus className="w-4 h-4" /> Connect new account
            </button>
          </div>
        </div>
      )}
    </div>
  );
}