/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'monospace'],
      },
      colors: {
        // Deep navy-black surface hierarchy
        canvas: {
          base:          '#06060f',  // app root — darkest
          muted:         '#0b0b18',  // sidebar, secondary panels
          surface:       '#0f0f1f',  // main content area
          card:          '#141428',  // cards, overlays
          overlay:       '#191935',  // raised elements, inputs
          border:        '#1e1e3a',  // default dividers
          'border-strong': '#2e2e58', // focused / hovered borders
          'text-dim':    '#363660',  // disabled, placeholders
          'text-muted':  '#6e6ea0',  // secondary labels
          'text-subtle': '#9898c0',  // metadata, hints
          text:          '#d5d5ee',  // primary content
          'text-bright': '#eeeef8',  // headings, emphasis
        },
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #5b21b6 0%, #7c3aed 60%, #6366f1 100%)',
        'gradient-user':  'linear-gradient(135deg, #6d28d9 0%, #7c3aed 55%, #5b5fcf 100%)',
      },
      boxShadow: {
        'glow-sm':  '0 0 12px rgba(124, 58, 237, 0.15)',
        'glow':     '0 0 24px rgba(124, 58, 237, 0.2)',
        'glow-lg':  '0 0 40px rgba(124, 58, 237, 0.25)',
        'card':     '0 1px 4px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.4)',
        'elevated': '0 4px 20px rgba(0,0,0,0.6)',
        'inset':    'inset 0 1px 0 rgba(255,255,255,0.03)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in':    'fadeIn 0.15s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
