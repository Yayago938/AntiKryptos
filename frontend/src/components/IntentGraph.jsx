import { useEffect, useRef } from "react";
import { Chart, RadarController, RadialLinearScale, PointElement, LineElement, Filler, Tooltip } from "chart.js";

Chart.register(RadarController, RadialLinearScale, PointElement, LineElement, Filler, Tooltip);

const LABELS = [
  "Urgency", "Authority", "Fear", "Credential",
  "Instr. Hijack", "Data Exfil", "Trust", "Identity",
  "Redirect", "Scarcity", "Payload", "Recon",
];

const KEYS = [
  "urgency_induction", "authority_spoof", "fear_amplification", "credential_harvesting",
  "instruction_hijack", "data_exfiltration", "trust_exploitation", "identity_spoofing",
  "redirect_chaining", "scarcity_signaling", "payload_delivery", "recon_probing",
];

const DEFAULT_SCORES = Object.fromEntries(KEYS.map((k) => [k, 0]));

export default function IntentGraph({ scores = DEFAULT_SCORES, animate = true }) {
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");

    // Gradient fill
    const gradient = ctx.createRadialGradient(
      canvasRef.current.width / 2, canvasRef.current.height / 2, 0,
      canvasRef.current.width / 2, canvasRef.current.height / 2, 200
    );
    gradient.addColorStop(0,   "rgba(0,255,136,0.25)");
    gradient.addColorStop(0.5, "rgba(0,212,255,0.12)");
    gradient.addColorStop(1,   "rgba(0,255,136,0.03)");

    chartRef.current = new Chart(ctx, {
      type: "radar",
      data: {
        labels: LABELS,
        datasets: [{
          label: "Intent Score",
          data: KEYS.map((k) => scores[k] ?? 0),
          backgroundColor: gradient,
          borderColor: "rgba(0,255,136,0.8)",
          borderWidth: 1.5,
          pointBackgroundColor: KEYS.map((k) =>
            (scores[k] ?? 0) >= 0.6 ? "#00ff88" : "#0a1628"
          ),
          pointBorderColor: KEYS.map((k) =>
            (scores[k] ?? 0) >= 0.6 ? "#00ff88" : "rgba(0,255,136,0.3)"
          ),
          pointRadius: KEYS.map((k) =>
            (scores[k] ?? 0) >= 0.6 ? 5 : 3
          ),
          pointHoverRadius: 7,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        animation: animate ? { duration: 900, easing: "easeOutQuart" } : false,
        scales: {
          r: {
            min: 0,
            max: 1,
            ticks: {
              stepSize: 0.25,
              display: false,
            },
            grid: {
              color: "rgba(0,255,136,0.07)",
              circular: false,
            },
            angleLines: {
              color: "rgba(0,255,136,0.08)",
            },
            pointLabels: {
              font: { family: "'JetBrains Mono'", size: 10 },
              color: (ctx) => {
                const val = KEYS.map((k) => scores[k] ?? 0)[ctx.index] ?? 0;
                return val >= 0.6 ? "#00ff88" : val >= 0.35 ? "#94a3b8" : "#475569";
              },
            },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(7,13,20,0.95)",
            borderColor: "rgba(0,255,136,0.3)",
            borderWidth: 1,
            titleFont: { family: "'JetBrains Mono'", size: 11 },
            bodyFont:  { family: "'JetBrains Mono'", size: 12 },
            titleColor: "#00ff88",
            bodyColor:  "#c8d8e8",
            callbacks: {
              title: (items) => items[0].label,
              label: (item) => ` ${(item.raw * 100).toFixed(0)}% confidence`,
            },
          },
        },
      },
    });

    return () => chartRef.current?.destroy();
  }, []);

  // Update data when scores change
  useEffect(() => {
    if (!chartRef.current) return;
    const ds = chartRef.current.data.datasets[0];
    ds.data = KEYS.map((k) => scores[k] ?? 0);
    ds.pointBackgroundColor = KEYS.map((k) =>
      (scores[k] ?? 0) >= 0.6 ? "#00ff88" : "#0a1628"
    );
    ds.pointBorderColor = KEYS.map((k) =>
      (scores[k] ?? 0) >= 0.6 ? "#00ff88" : "rgba(0,255,136,0.3)"
    );
    ds.pointRadius = KEYS.map((k) =>
      (scores[k] ?? 0) >= 0.6 ? 5 : 3
    );
    chartRef.current.update();
  }, [scores]);

  return (
    <div className="relative w-full aspect-square max-w-md mx-auto">
      {/* Outer ring decoration */}
      <div className="absolute inset-[-8px] rounded-full border border-neon-green/5 animate-spin" style={{ animationDuration: "30s" }} />
      <div className="absolute inset-[-20px] rounded-full border border-neon-green/3 animate-spin" style={{ animationDuration: "50s", animationDirection: "reverse" }} />
      <canvas ref={canvasRef} />
    </div>
  );
}
