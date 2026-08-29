import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0b0d",
          900: "#101114",
          800: "#17181c",
          700: "#212226",
          600: "#2c2d32",
          500: "#3c3d43",
          400: "#5a5b62",
          300: "#8a8b92",
          200: "#b7b8bf",
          100: "#e6e6ea",
        },
        win: {
          DEFAULT: "#22c55e",
          dim: "#14532d",
        },
        pending: {
          DEFAULT: "#f5a623",
          dim: "#5c4110",
        },
        lose: {
          DEFAULT: "#ef4444",
          dim: "#521717",
        },
        accent: {
          DEFAULT: "#4f7cff",
          bright: "#7099ff",
          dim: "#1c2a52",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      keyframes: {
        "pile-pop": {
          "0%": { transform: "scale(1)" },
          "40%": { transform: "scale(1.35)" },
          "100%": { transform: "scale(1)" },
        },
        "toast-in": {
          "0%": { transform: "translateY(-16px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(79,124,255,0.55)" },
          "100%": { boxShadow: "0 0 0 10px rgba(79,124,255,0)" },
        },
      },
      animation: {
        "pile-pop": "pile-pop 320ms cubic-bezier(.34,1.56,.64,1)",
        "toast-in": "toast-in 220ms ease-out",
        "pulse-ring": "pulse-ring 900ms ease-out",
      },
    },
  },
  plugins: [],
};
export default config;
