/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/templates/**/*.html',
    './src/apps/**/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0f172a',   // slate-900 — card backgrounds
          raised: '#1e293b',    // slate-800 — elevated cards / modals
        },
        accent: '#10b981',      // emerald-500 — primary actions
        danger: '#ef4444',      // red-500
        warning: '#fbbf24',     // amber-400
        success: '#34d399',     // emerald-400
        primary: {
          50: '#eff6ff',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'glow-emerald': '0 0 20px rgba(16,185,129,0.15)',
      },
    },
  },
  plugins: [],
};
