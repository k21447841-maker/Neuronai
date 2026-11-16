/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        nf: {
          bg: "#090B12",
          secondary: "#111522",
          card: "#171C2B",
          accent: "#8B5CF6",
          blue: "#3B82F6",
          text: "#F8FAFC",
          muted: "#94A3B8",
          success: "#22C55E",
          error: "#EF4444"
        }
      }
    }
  },
  plugins: []
};
