/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Fraunces", "Georgia", "serif"],
      },
      colors: {
        ink: {
          DEFAULT: "#141413",
          muted: "#6B675F",
          faint: "#9A958C",
        },
        paper: {
          DEFAULT: "#F3EFE8",
          raised: "#FFFcf7",
          line: "#E4DED4",
        },
        forest: {
          DEFAULT: "#1F6B4A",
          soft: "#E4F0EA",
          dark: "#3D9A6E",
        },
        clay: "#B45309",
        rose: "#9F2D3A",
      },
      boxShadow: {
        card: "0 1px 0 rgba(20,20,19,0.04), 0 12px 32px -20px rgba(20,20,19,0.18)",
        sheet: "0 -12px 40px rgba(20,20,19,0.16)",
      },
      borderRadius: {
        card: "1.15rem",
        sheet: "1.5rem",
      },
    },
  },
  plugins: [],
};
