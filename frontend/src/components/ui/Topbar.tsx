import React from "react";
import { RefreshCw } from "lucide-react";

interface Props {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
  loading?: boolean;
}

export const Topbar: React.FC<Props> = ({ title, subtitle, onRefresh, loading }) => (
  <div className="topbar">
    <div>
      <h1 className="topbar-title">{title}</h1>
      {subtitle && <p className="topbar-sub">{subtitle}</p>}
    </div>
    {onRefresh && (
      <button onClick={onRefresh} disabled={loading} className="refresh-btn">
        <RefreshCw size={14} style={loading ? { animation: "spin 0.8s linear infinite" } : {}} />
        Refresh
      </button>
    )}
  </div>
);
