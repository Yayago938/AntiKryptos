import { useRef, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import ParticleField from "./ParticleField";

const WORDS = ["Intelligence", "Defense", "Awareness", "Analysis"];

function TypeCycle() {
  const [idx, setIdx] = useState(0);
  const [display, setDisplay] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const word = WORDS[idx];
    let timeout;
    if (!deleting && display.length < word.length) {
      timeout = setTimeout(() => setDisplay(word.slice(0, display.length + 1)), 80);
    } else if (!deleting && display.length === word.length) {
      timeout = setTimeout(() => setDeleting(true), 2200);
    } else if (deleting && display.length > 0) {
      timeout = setTimeout(() => setDisplay(display.slice(0, -1)), 45);
    } else if (deleting && display.length === 0) {
      setDeleting(false);
      setIdx((i) => (i + 1) % WORDS.length);
    }
    return () => clearTimeout(timeout);
  }, [display, deleting, idx]);

  return (
    <span className="neon-text-green">
      {display}
      <span className="animate-pulse">_</span>
    </span>
  );
}

const STATS = [
  { label: "Threat Dimensions", value: "12" },
  { label: "Detection Accuracy", value: "94%" },
  { label: "Avg Response Time", value: "<50ms" },
  { label: "MITRE Techniques", value: "8+" },
];

export default function Hero() {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y     = useTransform(scrollYProgress, [0, 1], ["0%", "30%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);

  return (
    <section ref={ref} className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Cyber grid background */}
      <div className="absolute inset-0 cyber-grid-bg opacity-60" />

      {/* 3D particle canvas */}
      <div className="absolute inset-0">
        <ParticleField className="w-full h-full" />
      </div>

      {/* Radial glow behind title */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full bg-neon-green/5 blur-[100px] pointer-events-none" />

      {/* Content */}
      <motion.div
        style={{ y, opacity }}
        className="relative z-10 text-center px-6 max-w-5xl mx-auto"
      >
        {/* Status badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="inline-flex items-center gap-2.5 mb-8 px-4 py-2 rounded-full glass-panel border-neon-green/20"
        >
          <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
          <span className="font-mono text-xs tracking-[0.25em] text-slate-400 uppercase">
            System Online — Threat Monitoring Active
          </span>
        </motion.div>

        {/* Main heading */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="font-display font-extrabold text-6xl md:text-8xl tracking-tight text-white leading-[0.95] mb-4"
        >
          Anti
          <span className="block neon-text-green drop-shadow-[0_0_40px_rgba(0,255,136,0.5)]">
            Kryptos
          </span>
        </motion.h1>

        {/* Tagline with typewriter */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.7 }}
          className="font-display text-2xl md:text-3xl font-semibold text-slate-300 mb-3"
        >
          AI-Powered Cyber Threat{" "}
          <TypeCycle />
        </motion.p>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.75, duration: 0.7 }}
          className="text-slate-500 text-base md:text-lg max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          Detect adversarial intent across 12 psychological and technical dimensions.
          Powered by MITRE ATT&CK and Cialdini influence mapping.
        </motion.p>

        {/* CTA row */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9, duration: 0.6 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
        >
          <Link to="/analyze">
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="btn-primary text-sm px-10 py-3.5 glow-green"
            >
              ⬡ Launch Analyzer
            </motion.button>
          </Link>
          <a href="#features">
            <button className="btn-secondary text-sm px-8 py-3.5">
              Explore Platform ↓
            </button>
          </a>
        </motion.div>

        {/* Stats row */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.1, duration: 0.7 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-px bg-cyber-border/40 rounded-sm overflow-hidden border border-cyber-border/40"
        >
          {STATS.map(({ label, value }) => (
            <div key={label} className="bg-cyber-dark/80 px-6 py-4 text-center">
              <div className="font-mono text-2xl font-bold neon-text-green mb-1">{value}</div>
              <div className="font-mono text-xs text-slate-500 tracking-wider uppercase">{label}</div>
            </div>
          ))}
        </motion.div>
      </motion.div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
      >
        <span className="font-mono text-xs text-slate-600 tracking-widest uppercase">scroll</span>
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-px h-8 bg-gradient-to-b from-neon-green/60 to-transparent"
        />
      </motion.div>
    </section>
  );
}
