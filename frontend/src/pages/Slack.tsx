import React, { useState } from "react";
import { Topbar } from "../components/ui/Topbar";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = (path: string, method = "POST") =>
  fetch(`${BASE_URL}${path}`, { method }).then(r => r.json());

interface Result { success?: boolean; message?: string; error?: string; }

export const Slack: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, Result>>({});

  const call = async (key: string, path: string) => {
    setLoading(key);
    try {
      const res = await api(path);
      setResults(prev => ({ ...prev, [key]: res }));
    } catch (e: any) {
      setResults(prev => ({ ...prev, [key]: { success: false, error: e.message } }));
    } finally {
      setLoading(null);
    }
  };

  const actions = [
    {
      key: "test",
      title: "🔗 Test Connection",
      desc: "Send a test message to verify your Slack webhook is working correctly.",
      path: "/api/slack/test",
      color: "#2B6CB0", bg: "#EBF8FF", border: "#BEE3F8",
    },
    {
      key: "waste",
      title: "🚨 Send Waste Alert",
      desc: "Scan all resources and send a detailed waste detection report to Slack with resource links.",
      path: "/api/slack/waste-alert",
      color: "#C53030", bg: "#FFF5F5", border: "#FED7D7",
    },
    {
      key: "weekly",
      title: "📊 Send Weekly Summary",
      desc: "Send the weekly cost summary report with MTD spend, top services, and savings opportunities.",
      path: "/api/slack/weekly-summary",
      color: "#276749", bg: "#F0FFF4", border: "#9AE6B4",
    },
  ];

  return (
    <div>
      <Topbar title="Slack Integration" subtitle="Send cost alerts and weekly summaries to your Slack workspace" />

      {/* Setup instructions */}
      <div style={{ background: "#FFFBEB", border: "0.5px solid #FAF089", borderRadius: 12, padding: 18, marginBottom: 20 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: "#975A16", marginBottom: 8 }}>⚙️ Setup Required</h3>
        <p style={{ fontSize: 12, color: "#92400E", lineHeight: 1.7 }}>
          1. Go to <strong>api.slack.com/apps</strong> → Create New App → From Scratch<br />
          2. Enable <strong>Incoming Webhooks</strong> → Add to workspace → Copy webhook URL<br />
          3. Add to your backend environment variable: <code style={{ background: "#FEF3C7", padding: "1px 6px", borderRadius: 4, fontFamily: "monospace" }}>SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx</code><br />
          4. Redeploy backend → come back here and click <strong>Test Connection</strong>
        </p>
      </div>

      {/* Action cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 24 }}>
        {actions.map(action => {
          const res = results[action.key];
          const isLoading = loading === action.key;
          return (
            <div key={action.key} style={{ background: action.bg, border: `0.5px solid ${action.border}`, borderRadius: 14, padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: "#1e293b", marginBottom: 6 }}>{action.title}</h3>
                <p style={{ fontSize: 12, color: "#64748b", lineHeight: 1.6 }}>{action.desc}</p>
              </div>
              <button
                onClick={() => call(action.key, action.path)}
                disabled={isLoading}
                style={{
                  padding: "10px", background: action.color, color: "#fff",
                  border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600,
                  cursor: isLoading ? "not-allowed" : "pointer",
                  opacity: isLoading ? 0.7 : 1, marginTop: "auto",
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                }}
              >
                {isLoading ? (
                  <><span style={{ display: "inline-block", width: 14, height: 14, border: "2px solid rgba(255,255,255,0.4)", borderTopColor: "#fff", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} /> Sending...</>
                ) : "Send to Slack"}
              </button>
              {res && (
                <div style={{ padding: "8px 12px", borderRadius: 8, background: res.success !== false ? "rgba(39,103,73,0.1)" : "rgba(197,48,48,0.1)", fontSize: 11, color: res.success !== false ? "#276749" : "#C53030", fontWeight: 600 }}>
                  {res.success !== false ? `✅ ${res.message || "Sent successfully!"}` : `❌ ${res.error || "Failed"}`}
                </div>
              )}
            </div>
          );
        })}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); }}`}</style>

      {/* What gets sent preview */}
      <div style={{ background: "#1a1f2e", borderRadius: 14, padding: 20 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: "#94a3b8", marginBottom: 14 }}>👀 Preview — What Slack Messages Look Like</h3>
        <div style={{ background: "#fff", borderRadius: 10, padding: 16, marginBottom: 12 }}>
          <div style={{ display: "flex", gap: 10 }}>
            <div style={{ width: 36, height: 36, background: "#2563EB", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 700, fontSize: 16, flexShrink: 0 }}>$</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#1a1f2e" }}>FinOps Bot <span style={{ fontSize: 10, color: "#94a3b8", fontWeight: 400 }}>Today at 9:00 AM</span></div>
              <div style={{ fontSize: 13, color: "#1a1f2e", marginTop: 4, fontWeight: 600 }}>🚨 FinOps Waste Detection Alert</div>
              <div style={{ fontSize: 12, color: "#475569", marginTop: 4 }}>
                <strong>3 waste item(s) detected</strong> across your AWS account.<br />
                💰 <strong>Total potential savings: $18.60/month</strong>
              </div>
              <div style={{ marginTop: 10, padding: "8px 12px", background: "#f8fafc", borderRadius: 8, borderLeft: "3px solid #E53E3E", fontSize: 12, color: "#475569" }}>
                🔴 🖥️ <strong>EC2</strong> — <code>i-0a355d5ee2370b696</code><br />
                <em>Idle</em> · <strong>$15.00/mo savings</strong><br />
                Instance has avg CPU 1.2% over 7 days. Consider stopping.
                <br /><br />
                <span style={{ background: "#2563EB", color: "#fff", padding: "3px 10px", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>View in AWS</span>
              </div>
            </div>
          </div>
        </div>
        <p style={{ fontSize: 11, color: "#64748b", textAlign: "center" }}>Each resource gets an actionable button linking to AWS Console</p>
      </div>
    </div>
  );
};
