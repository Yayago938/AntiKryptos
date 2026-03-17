import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const LAYERS = [
  {
    number: "01",
    title: "Threat Input Layer",
    desc: "Accepts text, email, URL, PDF, image, VPN logs. Auto-detects type, strips PII, normalises Unicode zero-width chars and homoglyphs.",
    tags: ["PyMuPDF", "pytesseract", "regex"],
    color: "#00ff88",
  },
  {
    number: "02",
    title: "Prompt Security Gate",
    desc: "12ms fast-path filter. Keyword trie for instruction overrides, MinHash jailbreak matching, Indian PII patterns, hidden text scanner.",
    tags: ["~12ms", "Deterministic", "Lakera-inspired"],
    color: "#00d4ff",
  },
  {
    number: "03",
    title: "Adversarial Intent Graph",
    desc: "Fine-tuned DistilBERT with 12-label multi-label sigmoid head. Novel label schema fusing MITRE ATT&CK + Cialdini principles.",
    tags: ["DistilBERT", "BCEWithLogitsLoss", "12-dim"],
    color: "#00ff88",
  },
  {
    number: "04",
    title: "XAI Explainability Layer",
    desc: "Integrated gradients via Captum for token attribution. Kill chain mapper traverses intent graph → 5-stage narrative. DLP output scanner.",
    tags: ["Captum", "IntegratedGradients", "Kill Chain"],
    color: "#00d4ff",
  },
  {
    number: "05",
    title: "Response & Policy Engine",
    desc: "Per-organisation configurable thresholds. Hospital, bank, consumer profiles. Severity tiers: Low → Medium → High → Critical.",
    tags: ["FastAPI", "Configurable", "Per-org policy"],
    color: "#00ff88",
  },
];

export default function About() {
  const titleRef = useRef(null);
  const inV      = useInView(titleRef, { once: true });

  return (
    <section id="about" className="relative py-32 px-6 overflow-hidden">
      <div className="absolute inset-0 cyber-grid-bg opacity-20" />
      <div className="absolute left-1/2 top-0 w-px h-full bg-gradient-to-b from-transparent via-neon-green/10 to-transparent" />

      <div className="relative max-w-5xl mx-auto">
        <div ref={titleRef} className="text-center mb-20">
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={inV ? { opacity: 1, y: 0 } : {}}
            className="section-label mb-4"
          >
            // System Architecture
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={inV ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.1 }}
            className="font-display font-bold text-4xl md:text-5xl text-white"
          >
            Five layers. One{" "}
            <span className="neon-text-green">unified pipeline.</span>
          </motion.h2>
        </div>

        <div className="space-y-6">
          {LAYERS.map((layer, i) => (
            <motion.div
              key={layer.number}
              initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="glass-panel rounded-sm p-6 flex gap-6 hover:border-neon-green/20 transition-colors duration-300 group"
            >
              <div
                className="font-display font-extrabold text-5xl leading-none flex-shrink-0 w-14 transition-all duration-300"
                style={{
                  color: "transparent",
                  WebkitTextStroke: `1px ${layer.color}30`,
                }}
              >
                {layer.number}
              </div>
              <div className="flex-1">
                <h3 className="font-display font-semibold text-xl text-white mb-2">
                  {layer.title}
                </h3>
                <p className="text-slate-500 text-sm leading-relaxed mb-3">{layer.desc}</p>
                <div className="flex gap-2 flex-wrap">
                  {layer.tags.map((tag) => (
                    <span
                      key={tag}
                      className="font-mono text-[10px] tracking-wider px-2 py-0.5 rounded-sm border"
                      style={{
                        color:        layer.color,
                        background:   `${layer.color}10`,
                        borderColor:  `${layer.color}30`,
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Bottom stack info
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mt-16 glass-panel rounded-sm p-8 text-center"
        >
          <p className="section-label mb-4">// Tech Stack</p>
          <div className="flex flex-wrap justify-center gap-3">
            {["React + Vite", "FastAPI", "DistilBERT", "Framer Motion", "Three.js", "Chart.js", "Captum XAI", "Railway", "Vercel"].map((tech) => (
              <span
                key={tech}
                className="font-mono text-xs text-slate-400 bg-cyber-panel border border-cyber-border px-3 py-1.5 rounded-sm hover:border-neon-green/30 hover:text-neon-green transition-all duration-200"
              >
                {tech}
              </span>
            ))}
          </div>
        </motion.div> */}
      </div>
    </section>
  );
}