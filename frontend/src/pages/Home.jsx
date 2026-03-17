import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { Link } from "react-router-dom";
import Hero from "../components/Hero";
import FeatureCards from "../components/FeatureCards";
import About from "../components/About";

function SectionDivider({ flip = false }) {
  return (
    <div style={{
      position: "relative", height: "60px", overflow: "hidden",
      transform: flip ? "scaleX(-1)" : "none",
    }}>
      <motion.div
        initial={{ scaleX: 0 }}
        whileInView={{ scaleX: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
        style={{
          position: "absolute", top: "50%", left: 0, right: 0, height: "1px",
          background: "linear-gradient(90deg, transparent, rgba(0,255,136,0.4), transparent)",
          transformOrigin: "left",
        }}
      />
      <motion.div
        initial={{ x: "-10%" }}
        whileInView={{ x: "110%" }}
        viewport={{ once: true }}
        transition={{ duration: 1.6, delay: 0.3, ease: "easeInOut" }}
        style={{ position: "absolute", top: "50%", transform: "translateY(-50%)" }}
      >
        <div style={{ width: "8px", height: "8px", borderRadius: "50%",
          background: "#00ff88", boxShadow: "0 0 8px #00ff88" }} />
      </motion.div>
      <span style={{
        position: "absolute", left: "24px", top: "50%", transform: "translateY(-50%)",
        fontFamily: "'JetBrains Mono', monospace", fontSize: "10px",
        color: "rgba(30,45,61,1)", letterSpacing: "0.1em",
      }}>AntiKryptos</span>
      <span style={{
        position: "absolute", right: "24px", top: "50%", transform: "translateY(-50%)",
        fontFamily: "'JetBrains Mono', monospace", fontSize: "10px",
        color: "rgba(30,45,61,1)", letterSpacing: "0.1em",
      }}>SECURE</span>
    </div>
  );
}

export default function Home() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Hero />

      <SectionDivider />

      <motion.div
        initial={{ opacity: 0, y: 60 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
      >
        <FeatureCards />
      </motion.div>

      <SectionDivider flip />

      <motion.div
        initial={{ opacity: 0, x: -50 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
      >
        <About />
      </motion.div>

      {/* Footer */}
      <footer style={{
        borderTop: "1px solid rgba(15,45,74,0.4)",
        padding: "40px 24px",
        position: "relative",
      }}>
        <div style={{
          position: "absolute", inset: 0, opacity: 0.15, pointerEvents: "none",
          backgroundImage: "linear-gradient(rgba(0,255,136,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,136,0.03) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }} />
        <div style={{
          position: "relative", maxWidth: "1280px", margin: "0 auto",
          display: "flex", flexWrap: "wrap", alignItems: "center",
          justifyContent: "space-between", gap: "16px",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{
              width: "20px", height: "20px",
              border: "1px solid rgba(0,255,136,0.5)",
              transform: "rotate(45deg)",
            }} />
            <span style={{
              fontFamily: "'Syne', sans-serif", fontWeight: 700,
              letterSpacing: "0.12em", color: "#ffffff", fontSize: "15px",
            }}>
              Anti<span style={{ color: "#00ff88" }}>Kryptos</span>
            </span>
          </div>
          <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "#334155" }}>
           AntiKryptos | The Onestop Cyber Security Solution
          </p>
          <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "#1e293b" }}>
            Developing a cybersecurity platform for a safer digital future.
          </p>
        </div>
      </footer>
    </motion.div>
  );
}