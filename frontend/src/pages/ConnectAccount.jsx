import { useState, useEffect } from "react";
import { useAccount } from "../context/AccountContext";
import {
  Cloud, CheckCircle, Copy, ExternalLink,
  Loader2, AlertTriangle, ChevronRight, ChevronLeft, Shield
} from "lucide-react";

const REGIONS = [
  // USA
  "us-east-1",      // N. Virginia
  "us-east-2",      // Ohio
  "us-west-1",      // N. California
  "us-west-2",      // Oregon
  // Asia Pacific
  "ap-south-1",     // Mumbai
  "ap-south-2",     // Hyderabad
  "ap-southeast-1", // Singapore
  "ap-southeast-2", // Sydney
  "ap-southeast-3", // Jakarta
  "ap-southeast-4", // Melbourne
  "ap-northeast-1", // Tokyo
  "ap-northeast-2", // Seoul
  "ap-northeast-3", // Osaka
  "ap-east-1",      // Hong Kong
  // Europe
  "eu-west-1",      // Ireland
  "eu-west-2",      // London
  "eu-west-3",      // Paris
  "eu-central-1",   // Frankfurt
  "eu-central-2",   // Zurich
  "eu-north-1",     // Stockholm
  "eu-south-1",     // Milan
  "eu-south-2",     // Spain
  // Canada
  "ca-central-1",   // Canada Central
  "ca-west-1",      // Calgary
  // Middle East
  "me-south-1",     // Bahrain
  "me-central-1",   // UAE
  "il-central-1",   // Israel
  // Africa
  "af-south-1",     // Cape Town
  // South America
  "sa-east-1",      // São Paulo
];

export default function ConnectAccount({ onSuccess, onCancel }) {
  const { connectAccount, generateExternalId } = useAccount();

  const [step, setStep]             = useState(1);
  const [externalId, setExternalId] = useState("");
  const [trustPolicy, setTrustPolicy] = useState(null);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState("");
  const [copied, setCopied]         = useState("");

  const [form, setForm] = useState({
    account_name:   "",
    aws_account_id: "",
    role_arn:       "",
    default_region: "us-east-1",
  });

  useEffect(() => {
    generateExternalId().then(data => {
      setExternalId(data.external_id);
      setTrustPolicy(data.instructions?.trust_policy);
    }).catch(console.error);
  }, []);

  const copy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(""), 2000);
  };

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleConnect = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const result = await connectAccount(form);
      if (result.connection_status === "connected") {
        setStep(3);
        setTimeout(() => onSuccess?.(result), 1500);
      } else {
        setError(result.warning || "Connection failed. Please check your IAM role setup.");
      }
    } catch (err) {
      setError(err.message || "Connection failed");
    } finally {
      setLoading(false);
    }
  };

  const CodeBlock = ({ code, copyKey }) => (
    <div className="relative bg-gray-900 rounded-lg p-4 font-mono text-xs text-green-400 border border-gray-700">
      <pre className="whitespace-pre-wrap break-all pr-8">{code}</pre>
      <button onClick={() => copy(code, copyKey)}
        className="absolute top-3 right-3 text-gray-400 hover:text-white transition">
        {copied === copyKey ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
      </button>
    </div>
  );

  return (
    <div className="bg-gray-900 rounded-2xl border border-gray-700 max-w-2xl w-full mx-auto">

      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
            <Cloud className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-white font-bold text-lg">Connect AWS Account</h2>
            <p className="text-gray-400 text-sm">Secure cross-account IAM role connection</p>
          </div>
        </div>

        {/* Steps */}
        <div className="flex items-center gap-2 mt-5">
          {["Create IAM Role", "Enter Details", "Connected"].map((label, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition ${
                step === i + 1 ? "bg-blue-600 text-white" :
                step > i + 1  ? "bg-green-600 text-white" :
                "bg-gray-700 text-gray-400"
              }`}>
                {step > i + 1 ? <CheckCircle className="w-3 h-3" /> : <span>{i + 1}</span>}
                {label}
              </div>
              {i < 2 && <ChevronRight className="w-4 h-4 text-gray-600" />}
            </div>
          ))}
        </div>
      </div>

      <div className="p-6">

        {/* ── Step 1: IAM Setup ── */}
        {step === 1 && (
          <div className="space-y-5">
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 flex gap-3">
              <Shield className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-blue-300 font-medium text-sm">Secure by design</p>
                <p className="text-gray-400 text-xs mt-1">
                  We never ask for your AWS Access Keys. Instead, you create a read-only IAM role
                  in your account that our platform can temporarily assume.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-white font-semibold">Step 1 — Create IAM Role in your AWS account</h3>
              <div className="space-y-3">
                <p className="text-gray-300 text-sm">1. Go to <a href="https://console.aws.amazon.com/iam/home#/roles$new"
                  target="_blank" rel="noopener" className="text-blue-400 hover:underline inline-flex items-center gap-1">
                  AWS IAM Console → Roles → Create Role <ExternalLink className="w-3 h-3" />
                </a></p>
                <p className="text-gray-300 text-sm">2. Select <strong className="text-white">"Another AWS account"</strong></p>
                <p className="text-gray-300 text-sm">3. Enter the Platform Account ID — get this from your admin</p>
                <p className="text-gray-300 text-sm">4. Check <strong className="text-white">"Require external ID"</strong> and enter:</p>
                <CodeBlock code={externalId || "Generating..."} copyKey="extid" />
                <p className="text-gray-300 text-sm">5. Or use this complete trust policy:</p>
                {trustPolicy && (
                  <CodeBlock code={JSON.stringify(trustPolicy, null, 2)} copyKey="policy" />
                )}
                <p className="text-gray-300 text-sm">6. Attach policy: <strong className="text-white">ReadOnlyAccess</strong></p>
                <p className="text-gray-300 text-sm">7. Name the role: <strong className="text-white">FinOpsReadOnlyRole</strong></p>
                <p className="text-gray-300 text-sm">8. Copy the <strong className="text-white">Role ARN</strong> — you'll need it in Step 2</p>
              </div>
            </div>

            <button onClick={() => setStep(2)}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 rounded-lg transition flex items-center justify-center gap-2">
              I've created the role — Continue <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ── Step 2: Enter Details ── */}
        {step === 2 && (
          <form onSubmit={handleConnect} className="space-y-5">
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 flex gap-2 text-red-400 text-sm">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                {error}
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-gray-300 text-sm font-medium">Account Name</label>
              <input type="text" name="account_name" required
                value={form.account_name} onChange={handleChange}
                placeholder="Production, Development, Staging..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition" />
            </div>

            <div className="space-y-1.5">
              <label className="text-gray-300 text-sm font-medium">AWS Account ID</label>
              <input type="text" name="aws_account_id" required maxLength={12} minLength={12}
                value={form.aws_account_id} onChange={handleChange}
                placeholder="123456789012"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition font-mono" />
              <p className="text-gray-500 text-xs">12-digit AWS Account ID</p>
            </div>

            <div className="space-y-1.5">
              <label className="text-gray-300 text-sm font-medium">Role ARN</label>
              <input type="text" name="role_arn" required
                value={form.role_arn} onChange={handleChange}
                placeholder="arn:aws:iam::123456789012:role/FinOpsReadOnlyRole"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition font-mono text-sm" />
            </div>

            <div className="space-y-1.5">
              <label className="text-gray-300 text-sm font-medium">Default Region</label>
              <select name="default_region" value={form.default_region} onChange={handleChange}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-blue-500 transition">
                {REGIONS.map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>

            <div className="flex gap-3">
              <button type="button" onClick={() => setStep(1)}
                className="flex items-center gap-2 px-4 py-2.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition text-sm">
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <button type="submit" disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition flex items-center justify-center gap-2">
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? "Connecting..." : "Connect Account"}
              </button>
            </div>
          </form>
        )}

        {/* ── Step 3: Success ── */}
        {step === 3 && (
          <div className="text-center py-8 space-y-4">
            <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-8 h-8 text-green-400" />
            </div>
            <h3 className="text-white font-bold text-xl">Account Connected!</h3>
            <p className="text-gray-400 text-sm">
              Your AWS account has been successfully connected. Redirecting to dashboard...
            </p>
          </div>
        )}
      </div>

      {onCancel && step !== 3 && (
        <div className="px-6 pb-6">
          <button onClick={onCancel} className="w-full text-gray-400 hover:text-white text-sm transition">
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}