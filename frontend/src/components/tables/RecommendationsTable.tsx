import React, { useState } from "react";
import { ResourceRecommendation } from "../../types";
import { SeverityBadge } from "../ui/SeverityBadge";
import { ChevronDown, ChevronUp } from "lucide-react";

interface Props { data: ResourceRecommendation[]; }

export const RecommendationsTable: React.FC<Props> = ({ data }) => {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [filter, setFilter]     = useState("ALL");

  const types    = ["ALL", ...Array.from(new Set(data.map((r) => r.resource_type)))];
  const filtered = filter === "ALL" ? data : data.filter((r) => r.resource_type === filter);

  return (
    <div className="card">
      <div className="filter-bar">
        {types.map((t) => (
          <button key={t} onClick={() => setFilter(t)} className={`filter-btn${filter === t ? " active" : ""}`}>
            {t}
          </button>
        ))}
        <span className="filter-count">{filtered.length} item{filtered.length !== 1 ? "s" : ""}</span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Resource</th>
              <th>Type</th>
              <th>Region</th>
              <th>Issue</th>
              <th>Savings/mo</th>
              <th>Severity</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filtered.map((rec) => (
              <React.Fragment key={rec.resource_id}>
                <tr onClick={() => setExpanded(expanded === rec.resource_id ? null : rec.resource_id)}>
                  <td className="mono">{rec.resource_id}</td>
                  <td><span className={`type-badge type-${rec.resource_type}`}>{rec.resource_type}</span></td>
                  <td style={{ color: "#94a3b8", fontSize: 12 }}>{rec.region}</td>
                  <td style={{ textTransform: "capitalize", fontSize: 12 }}>{rec.issue}</td>
                  <td className="savings">${rec.estimated_monthly_savings.toFixed(2)}</td>
                  <td><SeverityBadge severity={rec.severity} /></td>
                  <td style={{ color: "#94a3b8" }}>
                    {expanded === rec.resource_id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </td>
                </tr>
                {expanded === rec.resource_id && (
                  <tr className="expanded-row">
                    <td colSpan={7}>
                      <p className="expanded-label">Recommendation</p>
                      <p className="expanded-text">{rec.recommendation}</p>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={7} className="no-data">No waste detected for this filter. 🎉</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
