import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, AlertTriangle, TrendingUp, FileDown,
  Bell, DollarSign, Moon, Sun, BellRing, Star,
  Zap, BarChart2, Slack
} from "lucide-react";

const nav = [
  { to: "/",           icon: LayoutDashboard, label: "Overview"        },
  { to: "/resources",  icon: AlertTriangle,   label: "Waste Detector"  },
  { to: "/trends",     icon: TrendingUp,      label: "Cost Trends"     },
  { to: "/budgets",    icon: Bell,            label: "Budget Alerts"   },
  { to: "/score",      icon: Star,            label: "Optim. Score"    },
  { to: "/anomalies",  icon: Zap,             label: "Anomalies"       },
  { to: "/forecast",   icon: BarChart2,       label: "Forecast"        },
  { to: "/alerts",     icon: BellRing,        label: "SNS Alerts"      },
  { to: "/slack",      icon: Slack,           label: "Slack"           },
  { to: "/reports",    icon: FileDown,        label: "Reports"         },
];

export const Sidebar: React.FC = () => {
  const [dark, setDark] = useState(() => localStorage.getItem("theme") === "dark");

  useEffect(() => {
    if (dark) {
      document.body.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.body.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [dark]);

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <DollarSign size={18} color="#fff" />
        </div>
        <div>
          <p className="sidebar-logo-title">FinOps</p>
          <p className="sidebar-logo-sub">Cost Optimizer</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div style={{ padding: "10px 12px 0" }}>
        <button
          onClick={() => setDark(!dark)}
          style={{
            width: "100%", display: "flex", alignItems: "center",
            justifyContent: "space-between", padding: "9px 12px",
            borderRadius: 10, border: "1px solid rgba(255,255,255,0.08)",
            background: "rgba(255,255,255,0.04)", cursor: "pointer",
            color: "#94a3b8", fontSize: 12, fontWeight: 500,
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 7 }}>
            {dark ? <Sun size={13} color="#fbbf24" /> : <Moon size={13} />}
            {dark ? "Light Mode" : "Dark Mode"}
          </span>
          <div style={{ width: 32, height: 18, borderRadius: 99, padding: 2, background: dark ? "#2563EB" : "rgba(255,255,255,0.1)", transition: "background 0.2s", display: "flex", alignItems: "center" }}>
            <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#fff", transform: dark ? "translateX(14px)" : "translateX(0)", transition: "transform 0.2s" }} />
          </div>
        </button>
      </div>

      <div className="sidebar-footer" style={{ marginTop: 10 }}>
        <p className="sidebar-footer-label">AWS Region</p>
        <p className="sidebar-footer-value">{import.meta.env.VITE_AWS_REGION || "us-east-1"}</p>
      </div>
    </aside>
  );
};
