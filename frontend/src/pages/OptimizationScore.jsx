import { useContext, useEffect, useState } from "react";
import { AccountContext } from "../context/AccountContext";

const API = import.meta.env.VITE_API_URL;

export default function OptimizationScore() {
  const { activeAccount, getAuthHeader } = useContext(AccountContext);
  const [score, setScore]     = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  useEffect(() => { if (activeAccount) fetchScore(); }, [activeAccount]);

  async function fetchScore() {
    setLoading(true);
    setError(null);
    try {
      const headers = await getAuthHeader();
      // /api/score — advanced.py mein yahi route hai
      const res = await fetch(`${API}/api/score?account_id=${activeAccount.aws_account_id}`, { headers });
      const json = await res.json();
      setScore(json);
    } catch (e) {
      console.error(e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (!activeAccount) return <div className="p-8 text-gray-400">Select an AWS account first.</div>;
  if (loading)        return <div className="p-8 text-gray-400">Computing score...</div>;
  if (error)          return <div className="p-8 text-red-400">Error: {error}</div>;
  if (!score)         return null;

  const gradeColor = {
    A: "text-green-400 border-green-400",
    B: "text-lime-400 border-lime-400",
    C: "text-yellow-400 border-yellow-400",
    D: "text-red-400 border-red-400",
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">🎯 Optimization Score</h1>
        <p className="text-gray-400 text-sm mt-1">{activeAccount.account_name}</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 flex flex-col items-center gap-4">
          <div className={`w-36 h-36 rounded-full border-4 flex flex-col items-center justify-center ${gradeColor[score.grade] ?? "text-gray-400 border-gray-400"}`}>
            <span className="text-5xl font-black text-white">{score.score}</span>
            <span className={`text-sm font-bold ${gradeColor[score.grade]?.split(' ')[0]}`}>
              Grade {score.grade}
            </span>
          </div>
          <p className="text-gray-400 text-sm text-center max-w-xs">{score.message}</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300">Score Breakdown</h2>
          {[
            ["Waste Score",   `${score.breakdown?.waste_score  ?? 0} / 50`],
            ["Issue Score",   `${score.breakdown?.issue_score  ?? 0} / 50`],
            ["Waste Ratio",   `${score.breakdown?.waste_ratio  ?? 0}%`],
            ["Total Issues",   score.breakdown?.issue_count ?? 0],
          ].map(([label, val]) => (
            <div key={label} className="bg-gray-800/50 rounded-lg p-3 flex justify-between items-center">
              <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
              <span className="text-lg font-bold text-white">{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}