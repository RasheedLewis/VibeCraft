import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        vc: {
          bg: '#0C0C12',
          surface: '#15151F',
          surfaceAlt: '#1C1C27',
          border: '#2A2A36',
          accent: {
            primary: '#6E6BFF',
            secondary: '#FF7EFA',
            tertiary: '#00E1D9',
          },
          text: {
            primary: '#FFFFFF',
            secondary: '#B6B6C9',
            muted: '#787891',
          },
          state: {
            error: '#FF5A75',
            warning: '#FFBD59',
          },
        },
      },
      borderRadius: {
        lg: '16px',
        md: '12px',
        sm: '8px',
      },
      boxShadow: {
        vc1: '0 1px 4px rgba(0,0,0,0.25)',
        vc2: '0 4px 12px rgba(0,0,0,0.35)',
        vc3: '0 8px 24px rgba(0,0,0,0.45)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'Inter', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        vcPulse: {
          '0%': { transform: 'scaleY(0.4)', opacity: '0.6' },
          '50%': { transform: 'scaleY(1)', opacity: '1' },
          '100%': { transform: 'scaleY(0.4)', opacity: '0.6' },
        },
      },
      animation: {
        vcPulse: 'vcPulse 1s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}

export default config
