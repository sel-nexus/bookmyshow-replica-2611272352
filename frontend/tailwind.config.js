/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: { cinema: { red: '#d71920', ink: '#111111', paper: '#fffaf8', smoke: '#3b3b3b' } },
      fontFamily: { display: ['Bebas Neue', 'sans-serif'], body: ['DM Sans', 'sans-serif'] }
    }
  },
  plugins: []
};
