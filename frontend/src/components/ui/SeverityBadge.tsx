import React from "react";

export const SeverityBadge: React.FC<{ severity: "HIGH" | "MEDIUM" | "LOW" }> = ({ severity }) => (
  <span className={`badge badge-${severity}`}>{severity}</span>
);
