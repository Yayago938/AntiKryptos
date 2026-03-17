import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";

const FEATURES = [
  {
    icon: "⬡",
    title: "Prompt Injection Detection",
    desc: "Identifies attempts to override AI system instructions using jailbreak patterns, DAN prompts, and instruction-override payloads.",
    tag: "MITRE T1059",
    color: "green",
  },
  {
    icon: "◈",
    title: "AI Phishing Detection",
    desc: "Analyzes text, email, and URL inputs for phishing signals — spear-phishing, credential lures, domain lookalikes.",
    tag: "MITRE T1566",
    color: "blue",
  },
  {
    icon: "◎",
    title: "Deep Intent Analysis",
    desc: "12-dimensional adversarial intent scoring fusing MITRE ATT&CK tactics with Cialdini psychological influence principles.",
    tag: "12 Dimensions",
    color: "green",
  },
  {
    icon: "◉",
    title: "Kill Chain Mapping",
    desc: "Maps detected threats to the Lockheed Martin Cyber Kill Chain — from Reconnaissance through Action on Objective.",
    tag: "Kill Chain",
    color: "blue",
  },
  {
    icon: "⬢",
    title: "Deep Fake Detector",
    desc: "Detecting deepfake images & flagging AI-generated content using a combination of metadata analysis, visual artifacts, and machine learning.",
    tag: "Interactive",
    color: "green",
  },
  {
    icon: "◇",
    title: "Explainable AI Scoring",
    desc: "Token-level attribution shows exactly which words triggered each intent dimension. Evidence-backed, not black-box.",
    tag: "XAI",
    color: "blue",
  },
];

const COLOR = {
  green: {
    border:  "border-neon-green/15 hover:border-neon-green/40",
    glow:    "group-hover:shadow-neon-green",
    icon:    "text-neon-green",
    tag:     "text-neon-green bg-neon-green/10 border border-neon-green/20",
    line:    "bg-neon-green",
  },
  blue: {
    border:  "border-neon-blue/15 hover:border-neon-blue/40",
    glow:    "group-hover:shadow-neon-blue",
    icon:    "text-neon-blue",
    tag:     "text-neon-blue bg-neon-blue/10 border border-neon-blue/20",
    line:    "bg-neon-blue",
  },
};

function FeatureCard({ feature, index }) {
  const ref  = useRef(null);
  const inV  = useInView(ref, { once: true, margin: "-60px" });
  const c    = COLOR[feature.color];

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 32 }}
      animate={inV ? { opacity: 1, y: 0 } : {}}
      transition={{ delay: index * 0.08, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={`group relative glass-panel rounded-sm p-6 transition-all duration-300 cursor-default ${c.border} ${c.glow}`}
    >
      {/* Top line accent */}
      <div className={`absolute top-0 left-6 right-6 h-px ${c.line} opacity-0 group-hover:opacity-50 transition-opacity duration-300`} />

      {/* Corner brackets on hover */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
        <div className={`absolute top-2 left-2 w-3 h-3 border-t border-l ${feature.color === "green" ? "border-neon-green/60" : "border-neon-blue/60"}`} />
        <div className={`absolute bottom-2 right-2 w-3 h-3 border-b border-r ${feature.color === "green" ? "border-neon-green/60" : "border-neon-blue/60"}`} />
      </div>

      {/* Icon */}
      <div className={`text-3xl mb-4 ${c.icon} transition-all duration-300 group-hover:scale-110 group-hover:drop-shadow-[0_0_12px_currentColor]`}>
        {feature.icon}
      </div>

      {/* Tag */}
      <span className={`inline-block font-mono text-[10px] tracking-widest uppercase px-2 py-0.5 rounded-sm mb-3 ${c.tag}`}>
        {feature.tag}
      </span>

      <h3 className="font-display font-semibold text-lg text-white mb-2 leading-tight">
        {feature.title}
      </h3>
      <p className="text-slate-500 text-sm leading-relaxed">{feature.desc}</p>
    </motion.div>
  );
}

export default function FeatureCards() {
  const titleRef = useRef(null);
  const inV      = useInView(titleRef, { once: true });

  return (
    <section id="features" className="relative py-32 px-6">
      {/* Background accent */}
      <div className="absolute inset-0 cyber-grid-bg opacity-30" />

      <div className="relative max-w-7xl mx-auto">
        <div ref={titleRef} className="text-center mb-16">
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={inV ? { opacity: 1, y: 0 } : {}}
            className="section-label mb-4"
          >
            // Platform Capabilities
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={inV ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.1 }}
            className="font-display font-bold text-4xl md:text-5xl text-white"
          >
            Built to outthink{" "}
            <span className="neon-text-green">the algorithm</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            animate={inV ? { opacity: 1 } : {}}
            transition={{ delay: 0.2 }}
            className="text-slate-500 mt-4 max-w-xl mx-auto"
          >
            Every feature maps to a real-world attack vector. No vague AI promises.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((f, i) => (
            <FeatureCard key={f.title} feature={f} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
