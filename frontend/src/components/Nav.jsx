import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.nav
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? "glass-panel border-b border-neon-green/10 py-3"
          : "bg-transparent py-5"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative w-8 h-8">
            <div className="absolute inset-0 border border-neon-green/60 rotate-45 group-hover:rotate-[135deg] transition-transform duration-700" />
            <div className="absolute inset-1.5 bg-neon-green/20 rotate-45 group-hover:bg-neon-green/40 transition-colors duration-300" />
          </div>
          <span className="font-display font-bold text-lg tracking-widest text-white">
            Anti<span className="text-neon-green">Kryptos</span>
          </span>
        </Link>

        {/* Links */}
        <div className="hidden md:flex items-center gap-8">
          {[
            { label: "Platform", href: "/#features" },
            { label: "Analyzer", href: "/analyze"   },
            { label: "DeepFake Detection",    href: "/deepfake"    },
            { label: "About",    href: "/#about"    },
          ].map(({ label, href }) => (
            <Link
              key={label}
              to={href}
              className={`font-mono text-xs tracking-widest uppercase transition-colors duration-200 ${
                location.pathname === href
                  ? "text-neon-green"
                  : "text-slate-400 hover:text-slate-100"
              }`}
            >
              {label}
            </Link>
          ))}
        </div>

        {/* CTA */}
        {user ? (
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-slate-500 hidden md:block truncate max-w-[160px]">
              {user.email}
            </span>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              onClick={logout}
              className="btn-secondary text-xs px-4 py-2"
            >
              Logout
            </motion.button>
          </div>
        ) : (
          <Link to="/login">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="btn-primary text-xs px-5 py-2"
            >
              Launch Analyzer
            </motion.button>
          </Link>
        )}
      </div>
    </motion.nav>
  );
}