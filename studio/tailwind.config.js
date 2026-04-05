/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"SF Mono"', '"Fira Code"', 'monospace'],
      },
      colors: {
        surface: {
          0: '#09090b',   // zinc-950 — app background
          1: '#18181b',   // zinc-900 — panels
          2: '#27272a',   // zinc-800 — raised surfaces / borders
          3: '#3f3f46',   // zinc-700 — dividers
        },
        accent: {
          DEFAULT: '#22d3ee',  // cyan-400
          dim: '#0891b2',      // cyan-600
          glow: '#06b6d414',   // cyan translucent
        },
        pass: '#34d399',    // emerald-400
        fail: '#f87171',    // rose-400
        warn: '#fbbf24',    // amber-400
      },
      animation: {
        'pulse-slow':  'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'fade-in':     'fadeIn 0.18s ease-out both',
        'fade-in-up':  'fadeInUp 0.22s ease-out both',
        'slide-down':  'slideDown 0.25s ease-out both',
        'board-open':  'boardOpen 0.3s cubic-bezier(0.16,1,0.3,1) both',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%':   { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%':   { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        boardOpen: {
          '0%':   { opacity: '0', transform: 'scale(0.96) translateY(12px)' },
          '100%': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
      },
      transitionProperty: {
        'width': 'width',
        'sidebar': 'width, opacity, transform',
      },
    },
  },
  plugins: [],
}
