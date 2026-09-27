/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: "#0b0f14",
          panel: "#121821",
          border: "#232d3a",
          text: "#d7e1ea",
          muted: "#7c8a9c",
        },
      },
    },
  },
  plugins: [],
};
