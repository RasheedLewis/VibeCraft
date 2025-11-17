import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      // Design system tokens will be added in later phases
      colors: {
        // Placeholder for design system colors
      },
    },
  },
  plugins: [],
}

export default config

