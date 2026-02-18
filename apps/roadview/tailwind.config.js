/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'hot-pink': '#FF1D6C',
        'amber': '#F5A623',
        'electric-blue': '#2979FF',
        'violet': '#9C27B0',
      },
    },
  },
  plugins: [],
}
