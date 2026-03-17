import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { signInWithEmailAndPassword, signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../firebase";

export default function Login() {
  const [email, setEmail]     = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async () => {
    setError("");
    if (!email || !password) { setError("Please fill in all fields."); return; }
    setLoading(true);
    try {
      await signInWithEmailAndPassword(auth, email, password);
      navigate("/analyze");
    } catch (e) {
      setError(e.message.replace("Firebase: ", "").replace(/\(auth.*\)\.?/, "").trim());
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setError("");
    setLoading(true);
    try {
      await signInWithPopup(auth, googleProvider);
      navigate("/analyze");
    } catch (e) {
      setError(e.message.replace("Firebase: ", "").replace(/\(auth.*\)\.?/, "").trim());
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cyber-dark flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 cyber-grid-bg opacity-40" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-neon-green/5 blur-[120px] pointer-events-none" />

      {/* Corner accents */}
      <div className="absolute top-8 left-8 w-16 h-16 border-t border-l border-neon-green/20" />
      <div className="absolute bottom-8 right-8 w-16 h-16 border-b border-r border-neon-green/20" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-3 mb-10 group">
          <div className="relative w-8 h-8">
            <div className="absolute inset-0 border border-neon-green/60 rotate-45 group-hover:rotate-[135deg] transition-transform duration-700" />
            <div className="absolute inset-1.5 bg-neon-green/20 rotate-45 group-hover:bg-neon-green/40 transition-colors duration-300" />
          </div>
          <span className="font-display font-bold text-xl tracking-widest text-white">
            Anti<span className="text-neon-green">Kryptos</span>
          </span>
        </Link>

        {/* Card */}
        <div className="glass-panel rounded-sm p-8 border border-cyber-border/60">
          {/* Header */}
          <div className="mb-8">
            <p className="font-mono text-[10px] tracking-widest text-neon-green uppercase mb-2">
              // Operator Authentication
            </p>
            <h1 className="font-display font-bold text-2xl text-white">
              Sign in to your account
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              Don't have an account?{" "}
              <Link to="/signup" className="text-neon-green hover:underline">
                Create one
              </Link>
            </p>
          </div>

          <div className="space-y-4">
            {/* Email */}
            <div>
              <label className="font-mono text-[10px] tracking-widest text-slate-500 uppercase mb-1.5 block">
                // Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                placeholder="operator@sentinel-x.ai"
                className="w-full bg-cyber-dark/80 border border-cyber-border rounded-sm px-4 py-3 font-mono text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-neon-green/50 focus:bg-cyber-dark transition-all duration-200"
              />
            </div>

            {/* Password */}
            <div>
              <label className="font-mono text-[10px] tracking-widest text-slate-500 uppercase mb-1.5 block">
                // Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                placeholder="••••••••••••"
                className="w-full bg-cyber-dark/80 border border-cyber-border rounded-sm px-4 py-3 font-mono text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-neon-green/50 focus:bg-cyber-dark transition-all duration-200"
              />
            </div>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="font-mono text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-sm px-3 py-2"
                >
                  ⚠ {error}
                </motion.p>
              )}
            </AnimatePresence>

            {/* Submit */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleLogin}
              disabled={loading}
              className="btn-primary w-full py-3 text-sm mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-3 h-3 border border-neon-green/50 border-t-neon-green rounded-full animate-spin" />
                  Authenticating...
                </span>
              ) : "⬡ Access System"}
            </motion.button>

            {/* Divider */}
            <div className="flex items-center gap-3 my-1">
              <div className="flex-1 h-px bg-cyber-border" />
              <span className="font-mono text-[10px] text-slate-600 tracking-widest">OR</span>
              <div className="flex-1 h-px bg-cyber-border" />
            </div>

            {/* Google */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleGoogle}
              disabled={loading}
              className="btn-secondary w-full py-3 text-sm flex items-center justify-center gap-3 disabled:opacity-50"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </motion.button>
          </div>
        </div>

        <p className="text-center font-mono text-[10px] text-slate-600 tracking-wider mt-6">
          AntiKryptos · CLASSIFIED ACCESS PORTAL · {new Date().getFullYear()}
        </p>
      </motion.div>
    </div>
  );
}