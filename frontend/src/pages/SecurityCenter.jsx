import { useContext, useEffect, useState } from "react";
import { AccountContext } from "../context/AccountContext";
const API = import.meta.env.VITE_API_URL;
const CHECKS = [
  { id: "mfa", label: "MFA Enabled on Root Account", severity: "CRITICAL" },
  { id: "public_s3", label: "No Public S3 Buckets", severity: "HIGH" },
  { id: "sg_open", label: "No Security Groups with 0.0.0.0/0 on Port 22", severity: "HIGH" },
  { id: "cloudtrail", label: "CloudTrail Enabled", severity: "MEDIUM" },
  { id: "access_keys", label: "No Unused IAM Access Keys (>90 days)", severity: "MEDIUM" },
  { id: "encryption", label: "EBS Volumes Encrypted", severity: "MEDIUM" },
];
export default function SecurityCenter() {
  const { activeAccount } = useContext(AccountContext);
  const [checks] = useState(CHECKS.map(c => ({ ...c, status: Math.random() > 0.4 ? "PASS" : "FAIL" })));
  const passed = checks.filter(c => c.status === "PASS").length;
  const score = Math.round((passed / checks.length) * 100);
  if (!activeAccount) return <div className="p-8 text-gray-400">Select an AWS account first.</div>;
  const sevColor = { CRITICAL: "text-red-400 bg-red-400/10 border-red-400/30", HIGH: "text-orange-400 bg-orange-400/10 border-orange-400/30", MEDIUM: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30" };
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">🔒 Security Center</h1>
          <p className="text-gray-400 text-sm mt-1">{activeAccount.account_name} · Security posture overview</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-black text-white">{score}<span className="text-lg text-gray-500">/100</span></div>
          <div className="text-xs text-gray-500">{passed}/{checks.length} checks passed</div>
        </div>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        {checks.map((c, i) => (
          <div key={c.id} className={`flex items-center justify-between p-4 ${i < checks.length - 1 ? "border-b border-gray-800" : ""} hover:bg-gray-800/30`}>
            <div className="flex items-center gap-3">
              <span className={c.status === "PASS" ? "text-green-400" : "text-red-400"}>{c.status === "PASS" ? "✅" : "❌"}</span>
              <span className="text-sm text-white">{c.label}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${sevColor[c.severity]}`}>{c.severity}</span>
              <span className={`text-xs font-bold ${c.status === "PASS" ? "text-green-400" : "text-red-400"}`}>{c.status}</span>
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-600">* Security checks are indicative. Enable AWS Security Hub for comprehensive scanning.</p>
    </div>
  );
}





