import React from "react";
import { AlertCircle } from "lucide-react";

export const ErrorBox: React.FC<{ message: string }> = ({ message }) => (
  <div className="error-box">
    <AlertCircle size={18} style={{ marginTop: 2, flexShrink: 0 }} />
    <div>
      <p className="error-title">Something went wrong</p>
      <p className="error-msg">{message}</p>
    </div>
  </div>
);
