import { motion } from "framer-motion";

const RISK_CONFIG = {
  LOW:      { color: "#00ff88", bg: "rgba(0,255,136,0.08)",   border: "rgba(0,255,136,0.25)",  label: "LOW",      bar: "w-1/4" },
  MEDIUM:   { color: "#f59e0b", bg: "rgba(245,158,11,0.08)",  border: "rgba(245,158,11,0.25)", label: "MEDIUM",   bar: "w-2/4" },
  HIGH:     { color: "#ff3366", bg: "rgba(255,51,102,0.08)",  border: "rgba(255,51,102,0.3)",  label: "HIGH",     bar: "w-3/4" },
  CRITICAL: { color: "#ff0055", bg: "rgba(255,0,85,0.1)",     border: "rgba(255,0,85,0.4)",    label: "CRITICAL", bar: "w-full" },
};

const STAGE_DESC = {
  "Reconnaissance":
    "Attacker is quietly mapping your environment — probing for names, tools, and internal contacts before striking.",
  "Weaponization":
    "A psychological payload is being crafted. Authority, urgency, and fear signals are being layered.",
  "Delivery":
    "The attack is being pushed toward the victim — via spoofed sender, malicious link, or infected attachment.",
  "Exploitation":
    "Active compromise underway. Credentials, AI instructions, or system access are being targeted right now.",
  "Action on Objective":
    "Final stage reached — data theft, credential harvest, or AI manipulation has been attempted.",
};

export default function RiskPanel({ riskLevel, riskScore, killChainStage, model }) {
  const cfg = RISK_CONFIG[riskLevel?.toUpperCase()] ?? RISK_CONFIG.LOW;
  //const pct = riskScore > 1 ? Math.round(riskScore / 100) : Math.round((riskScore ?? 0) * 100);

  return (
    <div className="space-y-4">
      {/* Risk level card */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="relative glass-panel rounded-sm p-5 overflow-hidden"
        style={{ borderColor: cfg.border, background: cfg.bg }}
      >
        {/* Animated corner */}
        <div className="absolute top-0 right-0 w-16 h-16 overflow-hidden">
          <div
            className="absolute -top-8 -right-8 w-16 h-16 rotate-45 opacity-20"
            style={{ background: cfg.color }}
          />
        </div>

        <div className="section-label mb-3" style={{ color: cfg.color }}>
          // THREAT LEVEL
        </div>
        <div
          className="font-display font-extrabold text-4xl tracking-widest mb-1"
          style={{ color: cfg.color, textShadow: `0 0 30px ${cfg.color}80` }}
        >
          {cfg.label}
        </div>
        <div className="font-mono text-xs text-slate-500 mb-4">
          Risk Score: {riskScore}/100
        </div>

        {/* Score bar */}
        <div className="h-1 bg-cyber-border rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${riskScore}%` }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
            className="h-full rounded-full"
            style={{ background: cfg.color, boxShadow: `0 0 8px ${cfg.color}` }}
          />
        </div>

        <div className="mt-3 font-mono text-[10px] text-slate-600 tracking-wider">
          Model: {model ?? "keyword"}
        </div>
      </motion.div>

      {/* Kill chain card */}
      {killChainStage && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="glass-panel rounded-sm p-5"
        >
          <div className="section-label mb-3">// KILL CHAIN STAGE</div>
          {["Reconnaissance","Weaponization","Delivery","Exploitation","Action on Objective"].map((stage, i) => {
            const stages = ["Reconnaissance","Weaponization","Delivery","Exploitation","Action on Objective"];
            const activeIdx = stages.indexOf(killChainStage);
            const isActive  = stage === killChainStage;
            const isPassed  = i < activeIdx;
            return (
              <div key={stage} className="flex items-center gap-3 mb-2 last:mb-0">
                <div
                  className="w-2 h-2 rounded-full flex-shrink-0 transition-all duration-300"
                  style={{
                    background: isActive ? "#00ff88" : isPassed ? "#00ff8880" : "#1a3a5c",
                    boxShadow: isActive ? "0 0 8px #00ff88" : "none",
                  }}
                />
                <span
                  className="font-mono text-xs transition-colors duration-300"
                  style={{ color: isActive ? "#00ff88" : isPassed ? "#475569" : "#1a3a5c" }}
                >
                  {stage}
                </span>
                {isActive && (
                  <span className="ml-auto font-mono text-[10px] text-neon-green bg-neon-green/10 border border-neon-green/20 px-2 py-0.5 rounded-sm">
                    ACTIVE
                  </span>
                )}
              </div>
            );
          })}

          {STAGE_DESC[killChainStage] && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="mt-4 text-xs text-slate-500 leading-relaxed border-t border-cyber-border pt-4"
            >
              {STAGE_DESC[killChainStage]}
            </motion.p>
          )}
        </motion.div>
      )}
    </div>
  );
}
