/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Dark precision-instrument palette
        bg: {
          primary: '#0F1117',
          secondary: '#161822',
          tertiary: '#1C1F2E',
          card: '#1A1D2D',
        },
        text: {
          primary: '#E8EAF0',
          secondary: '#9CA3AF',
          muted: '#6B7280',
        },
        accent: {
          green: '#4CAF7D',
          'green-light': '#5EC98D',
          'green-dark': '#3A8F63',
        },
        warn: {
          amber: '#F59E0B',
          'amber-light': '#FCD34D',
        },
        error: {
          red: '#EF4444',
          'red-light': '#FCA5A5',
        },
        status: {
          pending: '#6B7280',
          processing: '#3B82F6',
          completed: '#4CAF7D',
          failed: '#EF4444',
          quarantined: '#F59E0B',
        },
      },
      fontFamily: {
        heading: ['Fraunces', 'Georgia', 'serif'],
        body: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'Menlo', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
