import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { supabase } from "../lib/supabase";

export function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register" | "reset">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      if (mode === "login") {
        const { error: err } = await supabase.auth.signInWithPassword({ email, password });
        if (err) throw err;
        navigate("/");
      } else if (mode === "register") {
        const { error: err } = await supabase.auth.signUp({ email, password });
        if (err) throw err;
        setMessage("Check your inbox to verify your email address.");
      } else {
        const { error: err } = await supabase.auth.resetPasswordForEmail(email);
        if (err) throw err;
        setMessage("Password reset email sent.");
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  async function signInWithGoogle() {
    const { error: err } = await supabase.auth.signInWithOAuth({ provider: "google" });
    if (err) setError(err.message);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#090B12] p-4">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#171C2B] p-8 shadow-2xl">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#8B5CF6] to-[#3B82F6]">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white">NEUROFLOW AI</h1>
            <p className="text-xs text-[#94A3B8]">AI YouTube Production & Automation</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-[#94A3B8]">Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white outline-none focus:border-[#8B5CF6]" />
          </div>
          {mode !== "reset" && (
            <div>
              <label className="mb-1 block text-xs font-medium text-[#94A3B8]">Password</label>
              <input type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white outline-none focus:border-[#8B5CF6]" />
            </div>
          )}
          {error && <p className="rounded-lg bg-[#EF4444]/10 p-2.5 text-xs text-[#EF4444]">{error}</p>}
          {message && <p className="rounded-lg bg-[#22C55E]/10 p-2.5 text-xs text-[#22C55E]">{message}</p>}
          <button disabled={busy} type="submit" className="w-full rounded-lg bg-[#8B5CF6] py-2.5 text-sm font-medium text-white hover:bg-[#7C3AED] disabled:opacity-50">
            {busy ? "Processing..." : mode === "login" ? "Sign In" : mode === "register" ? "Create Account" : "Send Reset Link"}
          </button>
        </form>
        <button onClick={signInWithGoogle} className="mt-3 w-full rounded-lg border border-white/10 bg-[#111522] py-2.5 text-sm font-medium text-[#F8FAFC] hover:bg-white/5">
          Continue with Google
        </button>
        <div className="mt-5 flex justify-between text-xs text-[#94A3B8]">
          <button onClick={() => setMode(mode === "login" ? "register" : "login")} className="hover:text-white">{mode === "login" ? "Create account" : "Back to sign in"}</button>
          <button onClick={() => setMode("reset")} className="hover:text-white">Forgot password?</button>
        </div>
      </div>
    </div>
  );
}
