import React, { useEffect, useState } from "react";
import { getRecommendations } from "../lib/api";
import { ResourceSummary } from "../types";
import { RecommendationsTable } from "../components/tables/RecommendationsTable";
import { Topbar }   from "../components/ui/Topbar";
import { Loader }   from "../components/ui/Loader";
import { ErrorBox } from "../components/ui/ErrorBox";

export const Resources: React.FC = () => {
  const [data,    setData]    = useState<ResourceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

  const load = async () => {
    setLoading(true); setError("");
    try { setData(await getRecommendations()); }
    catch (e: any) { setError(e?.response?.data?.detail || e.message || "Failed"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  if (loading) return <Loader text="Scanning AWS resources for waste..." />;
  if (error)   return <ErrorBox message={error} />;
  if (!data)   return null;

  const high   = data.recommendations.filter(r => r.severity === "HIGH").length;
  const medium = data.recommendations.filter(r => r.severity === "MEDIUM").length;
  const low    = data.recommendations.filter(r => r.severity === "LOW").length;

  return (
    <div>
      <Topbar title="Waste Detector" subtitle="Idle, unattached, and unused AWS resources" onRefresh={load} loading={loading} />
      <div className="pills-row">
        <div className="pill pill-savings">
          <span className="pill-num">${data.total_estimated_savings.toFixed(2)}</span>
          <span className="pill-lbl">potential monthly savings</span>
        </div>
        <div className="pill pill-high">
          <span className="pill-num">{high}</span>
          <span className="pill-lbl">HIGH</span>
        </div>
        <div className="pill pill-medium">
          <span className="pill-num">{medium}</span>
          <span className="pill-lbl">MEDIUM</span>
        </div>
        <div className="pill pill-low">
          <span className="pill-num">{low}</span>
          <span className="pill-lbl">LOW</span>
        </div>
      </div>
      <RecommendationsTable data={data.recommendations} />
    </div>
  );
};
