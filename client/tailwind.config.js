/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0b0f19',
        surface: '#111827',
        card: 'rgba(30, 41, 59, 0.7)',
        accent: '#3b82f6',
        danger: '#ef4444',
        warning: '#f59e0b',
        success: '#10b981',
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow-blue': '0 0 20px -5px rgba(59, 130, 246, 0.5)',
        'glow-red': '0 0 20px -5px rgba(239, 68, 68, 0.5)',
        'glow-green': '0 0 20px -5px rgba(16, 185, 129, 0.5)',
      }
    },
  },
  plugins: [],
}
