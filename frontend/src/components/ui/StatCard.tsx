import React from "react";

interface Props {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  color: "blue" | "green" | "yellow" | "red";
}

export const StatCard: React.FC<Props> = ({ title, value, subtitle, icon, color }) => (
  <div className={`stat-card ${color}`}>
    <div className="stat-icon">{icon}</div>
    <div>
      <p className="stat-label">{title}</p>
      <p className="stat-value">{value}</p>
      {subtitle && <p className="stat-sub">{subtitle}</p>}
    </div>
  </div>
);
