import { motion } from "framer-motion";
import Analyzer from "../components/Analyzer";

export default function AnalyzerPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="min-h-screen pt-20 relative"
    >
      {/* Background grid */}
      <div className="fixed inset-0 cyber-grid-bg opacity-30 pointer-events-none" />
      {/* Top glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-neon-green/3 blur-[120px] pointer-events-none" />
      <div className="relative z-10">
        <Analyzer />
      </div>
    </motion.div>
  );
}
