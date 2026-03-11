import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "San Francisco",
          "Segoe UI",
          "sans-serif",
        ],
      },
      colors: {
        sand: {
          50:  "#faf8f4",
          100: "#f3ede3",
          200: "#e8dcc8",
          300: "#d9c7a8",
          400: "#c8ae85",
          500: "#b69468",
          600: "#9a7a54",
          700: "#7d6244",
          800: "#634f37",
          900: "#50402e",
        },
      },
    },
  },
  plugins: [],
};

export default config;
