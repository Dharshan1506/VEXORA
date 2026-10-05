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
        bg: {
          dark: '#070B19',
          card: 'rgba(13, 20, 42, 0.65)',
          panel: 'rgba(16, 26, 56, 0.55)',
          border: 'rgba(255, 255, 255, 0.08)'
        },
        cyan: {
          glow: '#00F0FF',
          accent: '#00B8D9'
        },
        violet: {
          glow: '#9D4EDD',
          accent: '#7B2CBF'
        },
        magenta: {
          glow: '#F72585'
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        'glow-cyan': '0 0 25px rgba(0, 240, 255, 0.3)',
        'glow-violet': '0 0 25px rgba(157, 78, 221, 0.3)',
        'glow-magenta': '0 0 25px rgba(247, 37, 133, 0.3)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      }
    },
  },
  plugins: [],
}
