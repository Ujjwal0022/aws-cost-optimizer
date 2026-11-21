import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider }    from "./context/AuthContext";
import { AccountProvider } from "./context/AccountContext";
import ProtectedRoute      from "./components/auth/ProtectedRoute";

// Auth
import Login          from "./pages/auth/Login";
import Signup         from "./pages/auth/Signup";
import ForgotPassword from "./pages/auth/ForgotPassword";

// App pages
import Overview          from "./pages/Overview";
import Accounts          from "./pages/Accounts";
import Recommendations   from "./pages/Recommendations";
import Remediation       from "./pages/Remediation";
import AuditLogs         from "./pages/AuditLogs";
import SecurityCenter    from "./pages/SecurityCenter";
import Resources         from "./pages/Resources";
import Trends            from "./pages/Trends";
import CostForecast      from "./pages/CostForecast";
import AnomalyDetection  from "./pages/AnomalyDetection";
import MultiRegion       from "./pages/MultiRegion";
import OptimizationScore from "./pages/OptimizationScore";
import Alerts            from "./pages/Alerts";
import Reports           from "./pages/Reports";

import Sidebar from "./components/ui/Sidebar";

function ProtectedLayout({ children }) {
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen bg-gray-950 text-white">
        <Sidebar />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AccountProvider>
        <BrowserRouter>
          <Routes>
            {/* Public */}
            <Route path="/login"           element={<Login />} />
            <Route path="/signup"          element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/"                element={<Navigate to="/dashboard" replace />} />

            {/* Protected */}
            <Route path="/dashboard"       element={<ProtectedLayout><Overview /></ProtectedLayout>} />
            <Route path="/accounts"        element={<ProtectedLayout><Accounts /></ProtectedLayout>} />
            <Route path="/recommendations" element={<ProtectedLayout><Recommendations /></ProtectedLayout>} />
            <Route path="/remediation"     element={<ProtectedLayout><Remediation /></ProtectedLayout>} />
            <Route path="/audit"           element={<ProtectedLayout><AuditLogs /></ProtectedLayout>} />
            <Route path="/security"        element={<ProtectedLayout><SecurityCenter /></ProtectedLayout>} />
            <Route path="/resources"       element={<ProtectedLayout><Resources /></ProtectedLayout>} />
            <Route path="/trends"          element={<ProtectedLayout><Trends /></ProtectedLayout>} />
            <Route path="/forecast"        element={<ProtectedLayout><CostForecast /></ProtectedLayout>} />
            <Route path="/anomalies"       element={<ProtectedLayout><AnomalyDetection /></ProtectedLayout>} />
            <Route path="/regions"         element={<ProtectedLayout><MultiRegion /></ProtectedLayout>} />
            <Route path="/score"           element={<ProtectedLayout><OptimizationScore /></ProtectedLayout>} />
            <Route path="/alerts"          element={<ProtectedLayout><Alerts /></ProtectedLayout>} />
            <Route path="/reports"         element={<ProtectedLayout><Reports /></ProtectedLayout>} />

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AccountProvider>
    </AuthProvider>
  );
}

