import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        prism: {
          deep:   "#10233d",
          ice:    "#e8f4f8",
          mint:   "#5cc8a1",
          amber:  "#ffbe55",
          coral:  "#ff6d5a",
          blue:   "#4891f7",
          purple: "#a78bfa",
          cyan:   "#22d3ee",
          dark:   "#050d1a",
        },
      },
      boxShadow: {
        glass:  "0 14px 34px rgba(16, 35, 61, 0.16)",
        "glow-mint":   "0 0 24px rgba(92, 200, 161, 0.25), 0 4px 16px rgba(0,0,0,0.4)",
        "glow-coral":  "0 0 24px rgba(255, 109, 90, 0.25), 0 4px 16px rgba(0,0,0,0.4)",
        "glow-blue":   "0 0 24px rgba(72, 145, 247, 0.25), 0 4px 16px rgba(0,0,0,0.4)",
        "glow-purple": "0 0 24px rgba(167, 139, 250, 0.25), 0 4px 16px rgba(0,0,0,0.4)",
      },
      fontFamily: {
        sans: ["Space Grotesk", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
