import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, AlertTriangle, TrendingUp,
  Bell, FileText, Brain, Globe, Award,
  DollarSign, LogOut, ChevronDown, Cloud,
  Lightbulb, Wrench, ClipboardList, Shield, Sparkles,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import AccountSelector from "./AccountSelector";

const navItems = [
  { to: "/dashboard",       icon: LayoutDashboard, label: "Overview"         },
  { to: "/accounts",        icon: Cloud,           label: "AWS Accounts"     },
  { to: "/resources",       icon: AlertTriangle,   label: "Waste Detector"   },
  { to: "/recommendations", icon: Lightbulb,       label: "Recommendations"  },
  { to: "/remediation",     icon: Wrench,          label: "Remediation"      },
  { to: "/audit",           icon: ClipboardList,   label: "Audit Logs"       },
  { to: "/security",        icon: Shield,          label: "Security Center"  },
  { to: "/trends",          icon: TrendingUp,      label: "Cost Trends"      },
  { to: "/forecast",        icon: TrendingUp,      label: "Forecast (ML)"    },
  { to: "/anomalies",       icon: Brain,           label: "AI Anomalies"     },
  { to: "/regions",         icon: Globe,           label: "Multi-Region"     },
  { to: "/score",           icon: Award,           label: "Efficiency Score" },
  { to: "/alerts",          icon: Bell,            label: "Alerts"           },
  { to: "/reports",         icon: FileText,        label: "Reports"          },
];

export default function Sidebar() {
  const { user, logout }        = useAuth();
  const navigate                = useNavigate();
  const [showMenu, setShowMenu] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <aside className="w-56 min-h-screen bg-gray-900 border-r border-gray-800 flex flex-col">

      {/* Logo */}
      <div className="p-5 border-b border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <DollarSign className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-white text-sm font-semibold leading-tight">FinOps</p>
            <p className="text-blue-400 text-xs">COST OPTIMIZER</p>
          </div>
        </div>
        <AccountSelector />
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} end={to === "/dashboard"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User Profile */}
      <div className="p-3 border-t border-gray-800">
        <div className="relative">
          <button onClick={() => setShowMenu(!showMenu)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition text-left">
            <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center shrink-0">
              <span className="text-white text-xs font-bold">
                {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-xs font-medium truncate">{user?.full_name || "User"}</p>
              <p className="text-gray-400 text-xs truncate">{user?.email}</p>
            </div>
            <ChevronDown className="w-3 h-3 text-gray-400 shrink-0" />
          </button>

          {showMenu && (
            <div className="absolute bottom-full left-0 right-0 mb-1 bg-gray-800 border border-gray-700 rounded-lg overflow-hidden shadow-lg">
              <button onClick={handleLogout}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-400 hover:bg-gray-700 transition">
                <LogOut className="w-4 h-4" /> Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

