import { useNavigate } from "react-router-dom";
import { Cloud, Plus, ArrowRight } from "lucide-react";
import { useAccount } from "../../context/AccountContext";

export default function NoAccountBanner() {
  const navigate             = useNavigate();
  const { accounts, hasAccounts } = useAccount();

  return (
    <div className="flex items-center justify-center min-h-96 p-6">
      <div className="text-center space-y-5 max-w-md">
        <div className="w-16 h-16 bg-blue-600/20 rounded-2xl flex items-center justify-center mx-auto">
          <Cloud className="w-8 h-8 text-blue-400" />
        </div>

        {!hasAccounts ? (
          <>
            <h2 className="text-white text-xl font-bold">Connect your AWS Account</h2>
            <p className="text-gray-400 text-sm">
              Connect an AWS account to start tracking costs, detecting waste, and optimizing your infrastructure.
            </p>
            <button onClick={() => navigate("/accounts")}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition">
              <Plus className="w-4 h-4" /> Connect AWS Account
            </button>
          </>
        ) : (
          <>
            <h2 className="text-white text-xl font-bold">Select an AWS Account</h2>
            <p className="text-gray-400 text-sm">
              Choose an AWS account from the selector in the sidebar to view its data.
            </p>
            <button onClick={() => navigate("/accounts")}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition">
              Manage Accounts <ArrowRight className="w-4 h-4" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

