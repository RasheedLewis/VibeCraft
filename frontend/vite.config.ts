import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  define: {
    // Replace __DEV_DEFAULT_API__ at build time
    // In production (mode === 'production'), this becomes null, completely removing localhost from the bundle
    // In development, this becomes the localhost URL string
    __DEV_DEFAULT_API__: mode === 'development' 
      ? JSON.stringify('http://localhost:8000/api/v1')
      : 'null',
  },
}))
