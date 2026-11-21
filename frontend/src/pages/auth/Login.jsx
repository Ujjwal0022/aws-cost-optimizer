import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, DollarSign, Loader2 } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function Login() {
  const { login, signup, loginWithGoogle } = useAuth();
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") await login(email, password);
      else await signup(email, password, fullName);
      nav("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const google = async () => {
    try { await loginWithGoogle(); } catch (err) { setError(err.message); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={submit} className="w-96 space-y-4 rounded-xl bg-white p-8 shadow">
        <div className="flex items-center gap-2">
          <DollarSign className="text-indigo-600" />
          <h1 className="text-2xl font-semibold">{mode === "login" ? "Login" : "Sign up"}</h1>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {mode === "signup" && (
          <input className="w-full rounded border p-2" placeholder="Full name"
            value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        )}
        <input className="w-full rounded border p-2" type="email" placeholder="Email"
          value={email} onChange={(e) => setEmail(e.target.value)} required />
        <div className="relative">
          <input className="w-full rounded border p-2 pr-10" type={show ? "text" : "password"}
            placeholder="Password" value={password}
            onChange={(e) => setPassword(e.target.value)} minLength={6} required />
          <button type="button" onClick={() => setShow(!show)}
            className="absolute right-2 top-2.5 text-gray-500">
            {show ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
        <button disabled={busy} className="flex w-full items-center justify-center rounded bg-indigo-600 p-2 text-white">
          {busy ? <Loader2 className="animate-spin" size={18} /> : mode === "login" ? "Login" : "Create account"}
        </button>
        <button type="button" onClick={google} className="w-full rounded border p-2">
          Continue with Google
        </button>
        <p className="text-center text-sm">
          <button type="button" className="text-indigo-600"
            onClick={() => setMode(mode === "login" ? "signup" : "login")}>
            {mode === "login" ? "Don't have an account? Sign up" : "Already have an account? Login"}
          </button>
        </p>
      </form>
    </div>
  );
}
