import { useContext, useEffect, useState } from "react";
import { AccountContext } from "../context/AccountContext";
const API = import.meta.env.VITE_API_URL;
export default function Resources() {
  const { activeAccount, getAuthHeader } = useContext(AccountContext);
  const [summary, setSummary] = useState(null);
  const [ec2, setEc2] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("summary");
  useEffect(() => { if (activeAccount) fetchData(); }, [activeAccount]);
  async function fetchData() {
    setLoading(true);
    try {
      const headers = await getAuthHeader();
      const acct = activeAccount.aws_account_id;
      const [sum, instances] = await Promise.all([
        fetch(`${API}/resources/summary?account_id=${acct}`, { headers }).then(r => r.json()),
        fetch(`${API}/resources/ec2?account_id=${acct}`, { headers }).then(r => r.json()),
      ]);
      setSummary(sum); setEc2(instances.instances || []);
    } catch(e) { console.error(e); } finally { setLoading(false); }
  }
  if (!activeAccount) return <div className="p-8 text-gray-400">Select an AWS account first.</div>;
  if (loading) return <div className="p-8 text-gray-400">Loading resources...</div>;
  const stateColor = { running: "text-green-400", stopped: "text-gray-400", terminated: "text-red-400" };
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">☁️ Resources</h1>
        <p className="text-gray-400 text-sm mt-1">{activeAccount.account_name} · Inventory</p>
      </div>
      {summary && (
        <div className="grid grid-cols-5 gap-3">
          {[["EC2", summary.ec2, "🖥️"], ["RDS", summary.rds, "🗄️"], ["S3", summary.s3, "🪣"], ["EBS", summary.ebs, "💾"], ["EIPs", summary.eips, "🌐"]].map(([label, val, icon]) => (
            <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
              <div className="text-2xl mb-1">{icon}</div>
              <div className="text-xl font-bold text-white">{val}</div>
              <div className="text-xs text-gray-500">{label}</div>
            </div>
          ))}
        </div>
      )}
      <div className="flex gap-2 border-b border-gray-800">
        {["summary", "ec2"].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-semibold transition-colors border-b-2 -mb-px ${tab === t ? "text-white border-indigo-500" : "text-gray-500 border-transparent hover:text-gray-300"}`}>
            {t === "summary" ? "Overview" : "EC2 Instances"}
          </button>
        ))}
      </div>
      {tab === "ec2" && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-gray-800">
              <th className="text-left p-3 text-xs text-gray-500 uppercase">Name</th>
              <th className="text-left p-3 text-xs text-gray-500 uppercase">Instance ID</th>
              <th className="text-left p-3 text-xs text-gray-500 uppercase">Type</th>
              <th className="text-left p-3 text-xs text-gray-500 uppercase">State</th>
            </tr></thead>
            <tbody>
              {ec2.map(i => (
                <tr key={i.instance_id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="p-3 text-white font-medium">{i.name}</td>
                  <td className="p-3 text-gray-400 font-mono text-xs">{i.instance_id}</td>
                  <td className="p-3 text-gray-300">{i.instance_type}</td>
                  <td className={`p-3 font-semibold ${stateColor[i.state] || "text-gray-400"}`}>{i.state}</td>
                </tr>
              ))}
              {ec2.length === 0 && <tr><td colSpan={4} className="p-8 text-center text-gray-500">No EC2 instances found</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}





