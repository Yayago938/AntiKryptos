/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        neon: {
          green: "#00ff88",
          blue:  "#00d4ff",
          red:   "#ff3366",
        },
        cyber: {
          black:  "#030508",
          dark:   "#070d14",
          navy:   "#0a1628",
          panel:  "#0d1f35",
          border: "#0f2d4a",
          muted:  "#1a3a5c",
        },
      },
      fontFamily: {
        display: ["'Syne'", "sans-serif"],
        mono:    ["'JetBrains Mono'", "monospace"],
        body:    ["'Outfit'", "sans-serif"],
      },
      animation: {
        "pulse-slow":   "pulse 4s cubic-bezier(0.4,0,0.6,1) infinite",
        "scan":         "scan 3s linear infinite",
        "grid-scroll":  "gridScroll 20s linear infinite",
        "flicker":      "flicker 0.15s infinite",
      },
      keyframes: {
        scan: {
          "0%":   { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        gridScroll: {
          "0%":   { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "0 60px" },
        },
        flicker: {
          "0%,100%": { opacity: 1 },
          "50%":     { opacity: 0.8 },
        },
      },
      backgroundImage: {
        "cyber-grid": "linear-gradient(rgba(0,255,136,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,136,0.03) 1px, transparent 1px)",
      },
      backgroundSize: {
        "cyber-grid": "60px 60px",
      },
      boxShadow: {
        "neon-green": "0 0 20px rgba(0,255,136,0.4), 0 0 40px rgba(0,255,136,0.15)",
        "neon-blue":  "0 0 20px rgba(0,212,255,0.4), 0 0 40px rgba(0,212,255,0.15)",
        "neon-red":   "0 0 20px rgba(255,51,102,0.4), 0 0 40px rgba(255,51,102,0.15)",
        "panel":      "0 0 0 1px rgba(0,255,136,0.08), 0 8px 32px rgba(0,0,0,0.6)",
      },
    },
  },
  plugins: [],
};
