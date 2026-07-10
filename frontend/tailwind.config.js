/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "oklch(97% 0.012 75)",
        card: "oklch(99% 0.006 75)",
        ink: "oklch(22% 0.02 55)",
        "ink-soft": "oklch(45% 0.02 55)",
        "ink-faint": "oklch(54% 0.015 55)",
        line: "oklch(87% 0.015 65)",
        "line-soft": "oklch(93% 0.01 65)",
        accent: "oklch(52% 0.13 45)",
        "accent-soft": "oklch(93% 0.035 55)",
      },
      boxShadow: {
        soft: "0 18px 40px rgb(30 25 15 / 0.08)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
