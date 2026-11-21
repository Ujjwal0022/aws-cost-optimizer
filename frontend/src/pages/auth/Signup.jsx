import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Eye, EyeOff, DollarSign, Loader2, CheckCircle } from "lucide-react";

export default function Signup() {
  const { signup, verifyEmail } = useAuth();
  const navigate = useNavigate();

  const [step, setStep]     = useState("signup");  // "signup" | "verify"
  const [form, setForm]     = useState({ email: "", password: "", fullName: "" });
  const [code, setCode]     = useState("");
  const [error, setError]   = useState("");
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setLoading(true);
    try {
      await signup(form.email, form.password, form.fullName);
      setStep("verify");
    } catch (err) {
      setError(err.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await verifyEmail(form.email, code);
      navigate("/login", { state: { message: "Email verified! Please login." } });
    } catch (err) {
      setError(err.message || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">

        {/* Logo */}
        <div className="text-center">
          <div className="inline-flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-white" />
            </div>
            <div className="text-left">
              <p className="text-white font-bold text-lg leading-tight">FinOps</p>
              <p className="text-blue-400 text-xs tracking-widest">COST OPTIMIZER</p>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white">
            {step === "signup" ? "Create your account" : "Verify your email"}
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            {step === "signup"
              ? "Start optimizing your AWS costs today"
              : `We sent a code to ${form.email}`}
          </p>
        </div>

        <div className="bg-gray-900 rounded-2xl p-8 border border-gray-800 space-y-5">

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* ── Signup Form ── */}
          {step === "signup" && (
            <form onSubmit={handleSignup} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-gray-300 text-sm font-medium">Full Name</label>
                <input type="text" name="fullName" required
                  value={form.fullName} onChange={handleChange}
                  placeholder="Ujjwal Kumar"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-gray-300 text-sm font-medium">Email</label>
                <input type="email" name="email" required
                  value={form.email} onChange={handleChange}
                  placeholder="you@company.com"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-gray-300 text-sm font-medium">Password</label>
                <div className="relative">
                  <input type={showPw ? "text" : "password"} name="password" required
                    value={form.password} onChange={handleChange}
                    placeholder="Min 8 characters"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition pr-11"
                  />
                  <button type="button" onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200">
                    {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-gray-500 text-xs">
                  Must contain uppercase, lowercase, number and special character
                </p>
              </div>

              <button type="submit" disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition flex items-center justify-center gap-2">
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? "Creating account..." : "Create account"}
              </button>

              <p className="text-center text-gray-400 text-sm">
                Already have an account?{" "}
                <Link to="/login" className="text-blue-400 hover:underline font-medium">
                  Sign in
                </Link>
              </p>
            </form>
          )}

          {/* ── Verify Form ── */}
          {step === "verify" && (
            <form onSubmit={handleVerify} className="space-y-4">
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                <p className="text-blue-300 text-sm">
                  Account created! Check your email for a 6-digit verification code.
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="text-gray-300 text-sm font-medium">Verification Code</label>
                <input type="text" required maxLength={6}
                  value={code} onChange={(e) => setCode(e.target.value)}
                  placeholder="123456"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition text-center text-xl tracking-widest font-mono"
                />
              </div>

              <button type="submit" disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition flex items-center justify-center gap-2">
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? "Verifying..." : "Verify Email"}
              </button>

              <button type="button" onClick={() => setStep("signup")}
                className="w-full text-gray-400 hover:text-white text-sm transition">
                ← Back to signup
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

