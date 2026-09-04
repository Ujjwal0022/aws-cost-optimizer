import React, { useEffect, useState } from "react";
import { Topbar } from "../components/ui/Topbar";
import { Loader } from "../components/ui/Loader";
import { ErrorBox } from "../components/ui/ErrorBox";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = (path: string, opts?: RequestInit) =>
  fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  }).then((r) => r.json());

interface Subscription {
  email: string;
  status: "confirmed" | "pending";
  arn: string;
}

interface Alarm {
  alarm_name: string;
  state: "OK" | "ALARM" | "INSUFFICIENT_DATA";
  description: string;
  threshold: number;
  last_updated: string;
}

interface ScanResult {
  total_alerts_sent: number;
  ec2_alarms_created: number;
  ebs_alerts_sent: number;
  eip_alerts_sent: number;
}

const STATE_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  ALARM:             { bg: "#FFF5F5", text: "#C53030", label: "🔴 ALARM"   },
  OK:                { bg: "#F0FFF4", text: "#276749", label: "🟢 OK"      },
  INSUFFICIENT_DATA: { bg: "#FFFBEB", text: "#975A16", label: "🟡 NO DATA" },
};

export const Alerts: React.FC = () => {
  const [email,         setEmail]         = useState("");
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [alarms,        setAlarms]        = useState<Alarm[]>([]);
  const [scanResult,    setScanResult]    = useState<ScanResult | null>(null);
  const [loading,       setLoading]       = useState(false);
  const [scanLoading,   setScanLoading]   = useState(false);
  const [subLoading,    setSubLoading]    = useState(false);
  const [error,         setError]         = useState("");
  const [successMsg,    setSuccessMsg]    = useState("");

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [subs, alrms] = await Promise.all([
        api("/api/alerts/subscriptions"),
        api("/api/alerts/alarms"),
      ]);
      setSubscriptions(Array.isArray(subs) ? subs : []);
      setAlarms(Array.isArray(alrms) ? alrms : []);
    } catch (e: any) {
      setError(e.message || "Failed to load alert data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleSubscribe = async () => {
    if (!email) return;
    setSubLoading(true);
    setError(""); setSuccessMsg("");
    try {
      const res = await api("/api/alerts/subscribe", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setSuccessMsg(res.message || "Confirmation email sent! Please check your inbox.");
      setEmail("");
      loadData();
    } catch (e: any) {
      setError(e.message || "Subscription failed");
    } finally {
      setSubLoading(false);
    }
  };

  const handleUnsubscribe = async (arn: string) => {
    try {
      await api("/api/alerts/unsubscribe", {
        method: "DELETE",
        body: JSON.stringify({ subscription_arn: arn }),
      });
      setSuccessMsg("Unsubscribed successfully.");
      loadData();
    } catch (e: any) {
      setError(e.message || "Unsubscribe failed");
    }
  };

  const handleScanAndAlert = async () => {
    setScanLoading(true);
    setError(""); setSuccessMsg("");
    try {
      const res = await api("/api/alerts/scan-and-alert", { method: "POST" });
      setScanResult(res);
      setSuccessMsg(`Scan complete! ${res.total_alerts_sent} alert(s) sent.`);
      loadData();
    } catch (e: any) {
      setError(e.message || "Scan failed");
    } finally {
      setScanLoading(false);
    }
  };

  const handleDeleteAlarm = async (alarmName: string) => {
    const instanceId = alarmName.replace("finops-idle-ec2-", "");
    try {
      await api(`/api/alerts/ec2/alarm/${instanceId}`, { method: "DELETE" });
      setSuccessMsg("Alarm deleted.");
      loadData();
    } catch (e: any) {
      setError(e.message || "Delete failed");
    }
  };

  if (loading) return <Loader text="Loading alert configuration..." />;

  return (
    <div>
      <Topbar
        title="SNS Alert Center"
        subtitle="Get notified when idle or wasted AWS resources are detected"
        onRefresh={loadData}
        loading={loading}
      />

      {/* Success message */}
      {successMsg && (
        <div style={{ background: "#F0FFF4", border: "0.5px solid #9AE6B4", borderRadius: 10, padding: "12px 16px", marginBottom: 16, fontSize: 13, color: "#276749", display: "flex", alignItems: "center", gap: 8 }}>
          ✅ {successMsg}
        </div>
      )}

      {/* Error */}
      {error && <div style={{ marginBottom: 16 }}><ErrorBox message={error} /></div>}

      {/* ── Section 1: Email Subscribe ── */}
      <div style={{ background: "#fff", borderRadius: 12, padding: 20, border: "0.5px solid #f1f5f9", marginBottom: 16, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: "#1e293b", marginBottom: 4 }}>📧 Email Notifications</h3>
        <p style={{ fontSize: 12, color: "#94a3b8", marginBottom: 16 }}>
          Subscribe your email to receive alerts when idle EC2, unattached EBS, or unused Elastic IPs are detected.
        </p>

        <div style={{ display: "flex", gap: 10 }}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your-email@example.com"
            onKeyDown={(e) => e.key === "Enter" && handleSubscribe()}
            style={{ flex: 1, padding: "9px 14px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13, outline: "none", fontFamily: "inherit" }}
          />
          <button
            onClick={handleSubscribe}
            disabled={subLoading || !email}
            style={{ padding: "9px 20px", background: "#2563EB", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: subLoading || !email ? "not-allowed" : "pointer", opacity: subLoading || !email ? 0.6 : 1 }}
          >
            {subLoading ? "Subscribing..." : "Subscribe"}
          </button>
        </div>

        {/* Active subscriptions */}
        {subscriptions.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <p style={{ fontSize: 11, fontWeight: 600, color: "#64748b", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>Active Subscriptions</p>
            {subscriptions.map((sub) => (
              <div key={sub.arn} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", background: "#f8fafc", borderRadius: 8, marginBottom: 6 }}>
                <div>
                  <span style={{ fontSize: 13, color: "#334155" }}>{sub.email}</span>
                  <span style={{ marginLeft: 8, padding: "1px 8px", borderRadius: 99, fontSize: 10, fontWeight: 600, background: sub.status === "confirmed" ? "#C6F6D5" : "#FEFCBF", color: sub.status === "confirmed" ? "#276749" : "#975A16" }}>
                    {sub.status === "confirmed" ? "✓ Confirmed" : "⏳ Pending"}
                  </span>
                </div>
                {sub.arn !== "PendingConfirmation" && (
                  <button
                    onClick={() => handleUnsubscribe(sub.arn)}
                    style={{ fontSize: 11, color: "#EF4444", background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}
                  >
                    Unsubscribe
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Section 2: Scan & Alert ── */}
      <div style={{ background: "#fff", borderRadius: 12, padding: 20, border: "0.5px solid #f1f5f9", marginBottom: 16, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: "#1e293b", marginBottom: 4 }}>🔍 Scan & Alert Now</h3>
        <p style={{ fontSize: 12, color: "#94a3b8", marginBottom: 16 }}>
          Scan all resources immediately and send email alerts for any waste detected. Also creates CloudWatch alarms for idle EC2 instances.
        </p>

        {/* What gets scanned */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 16 }}>
          {[
            { icon: "🖥️", type: "EC2", desc: "CPU < 5% for 1.5 hrs", action: "CloudWatch alarm created" },
            { icon: "💾", type: "EBS", desc: "Unattached volumes",    action: "Instant SNS notification" },
            { icon: "🌐", type: "EIP", desc: "Unused Elastic IPs",    action: "Instant SNS notification" },
          ].map((item) => (
            <div key={item.type} style={{ background: "#f8fafc", borderRadius: 10, padding: 12, border: "0.5px solid #e2e8f0" }}>
              <div style={{ fontSize: 20, marginBottom: 6 }}>{item.icon}</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#334155" }}>{item.type}</div>
              <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 2 }}>{item.desc}</div>
              <div style={{ fontSize: 10, color: "#2563EB", marginTop: 4, fontWeight: 600 }}>{item.action}</div>
            </div>
          ))}
        </div>

        <button
          onClick={handleScanAndAlert}
          disabled={scanLoading}
          style={{ width: "100%", padding: "10px", background: scanLoading ? "#93C5FD" : "#2563EB", color: "#fff", border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: scanLoading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
        >
          {scanLoading ? (
            <><span style={{ display: "inline-block", width: 14, height: 14, border: "2px solid rgba(255,255,255,0.4)", borderTopColor: "#fff", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} /> Scanning AWS resources...</>
          ) : (
            "🚀 Scan All Resources & Send Alerts"
          )}
        </button>
        <style>{`@keyframes spin { to { transform: rotate(360deg); }}`}</style>

        {/* Scan results */}
        {scanResult && (
          <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
            {[
              { label: "Total Alerts", value: scanResult.total_alerts_sent,   color: "#2563EB" },
              { label: "EC2 Alarms",   value: scanResult.ec2_alarms_created,  color: "#7C3AED" },
              { label: "EBS Alerts",   value: scanResult.ebs_alerts_sent,     color: "#059669" },
              { label: "EIP Alerts",   value: scanResult.eip_alerts_sent,     color: "#D97706" },
            ].map((s) => (
              <div key={s.label} style={{ background: "#f8fafc", borderRadius: 8, padding: "10px 12px", textAlign: "center", border: "0.5px solid #e2e8f0" }}>
                <div style={{ fontSize: 22, fontWeight: 900, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Section 3: Active CloudWatch Alarms ── */}
      <div style={{ background: "#fff", borderRadius: 12, border: "0.5px solid #f1f5f9", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
        <div style={{ padding: "14px 20px", borderBottom: "0.5px solid #f1f5f9", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: "#1e293b" }}>🔔 Active CloudWatch Alarms</h3>
            <p style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>EC2 idle alarms created by FinOps</p>
          </div>
          <span style={{ fontSize: 11, color: "#94a3b8" }}>{alarms.length} alarm{alarms.length !== 1 ? "s" : ""}</span>
        </div>

        {alarms.length === 0 ? (
          <div style={{ padding: 32, textAlign: "center", color: "#94a3b8", fontSize: 13 }}>
            No active alarms. Click "Scan All Resources" to create alarms for idle EC2 instances.
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ background: "#f8fafc" }}>
                {["Resource", "State", "Threshold", "Last Updated", "Action"].map((h) => (
                  <th key={h} style={{ padding: "8px 14px", textAlign: "left", fontSize: 10, fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {alarms.map((alarm) => {
                const stateStyle = STATE_STYLE[alarm.state] || STATE_STYLE["INSUFFICIENT_DATA"];
                const instanceId = alarm.alarm_name.replace("finops-idle-ec2-", "");
                return (
                  <tr key={alarm.alarm_name} style={{ borderTop: "0.5px solid #f8fafc" }}>
                    <td style={{ padding: "10px 14px" }}>
                      <div style={{ fontFamily: "monospace", fontSize: 11, color: "#334155" }}>{instanceId}</div>
                      <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 2 }}>EC2 Instance</div>
                    </td>
                    <td style={{ padding: "10px 14px" }}>
                      <span style={{ padding: "3px 10px", borderRadius: 99, fontSize: 10, fontWeight: 700, background: stateStyle.bg, color: stateStyle.text }}>
                        {stateStyle.label}
                      </span>
                    </td>
                    <td style={{ padding: "10px 14px", color: "#475569" }}>
                      CPU &lt; {alarm.threshold}%
                    </td>
                    <td style={{ padding: "10px 14px", color: "#94a3b8", fontSize: 11 }}>
                      {new Date(alarm.last_updated).toLocaleDateString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td style={{ padding: "10px 14px" }}>
                      <button
                        onClick={() => handleDeleteAlarm(alarm.alarm_name)}
                        style={{ fontSize: 11, color: "#EF4444", background: "#FFF5F5", border: "0.5px solid #FED7D7", borderRadius: 6, padding: "4px 10px", cursor: "pointer", fontWeight: 600 }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Info box */}
      <div style={{ background: "#EBF8FF", border: "0.5px solid #BEE3F8", borderRadius: 10, padding: 14, marginTop: 16 }}>
        <p style={{ fontSize: 12, color: "#2B6CB0", fontWeight: 600, marginBottom: 4 }}>ℹ️ How alerts work</p>
        <p style={{ fontSize: 11, color: "#3182CE", lineHeight: 1.6 }}>
          <strong>EC2:</strong> CloudWatch monitors CPU utilization every 30 minutes. If below 5% for 3 consecutive periods (1.5 hrs), an email alert fires.<br />
          <strong>EBS & EIP:</strong> Instant SNS notification sent when unattached/unused resources are detected during a scan.<br />
          <strong>First time:</strong> You must confirm the subscription email from AWS before alerts are delivered.
        </p>
      </div>
    </div>
  );
};
