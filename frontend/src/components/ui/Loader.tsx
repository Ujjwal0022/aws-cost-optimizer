import React from "react";

export const Loader: React.FC<{ text?: string }> = ({ text = "Loading..." }) => (
  <div className="loader-wrap">
    <div className="spinner" />
    <p className="loader-text">{text}</p>
  </div>
);
