/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F3EEE4",
        ink: "#1C1916",
        mute: "#6B645B",
        line: "#DDD4C6",
        copper: "#C26A3A",
        forest: "#3F5C4E",
        cream: "#FAF7F1",
      },
      fontFamily: {
        serif: ["Fraunces", "Georgia", "serif"],
        sans: ["Outfit", "system-ui", "sans-serif"],
      },
      boxShadow: {
        sheet: "0 24px 60px -28px rgba(28, 25, 22, 0.28)",
      },
    },
  },
  plugins: [],
};
