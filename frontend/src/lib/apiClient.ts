import axios from 'axios'

// Use build-time replacement to completely exclude localhost from production builds
// Vite will replace __DEV_DEFAULT_API__ at build time, ensuring localhost never appears in production bundle
// In production: __DEV_DEFAULT_API__ becomes null, so DEFAULT_API_BASE_URL becomes null
// In development: __DEV_DEFAULT_API__ becomes the localhost URL string
const DEFAULT_API_BASE_URL: string | null = __DEV_DEFAULT_API__

const normalizeBaseUrl = (rawUrl: string | undefined): string => {
  if (!rawUrl) {
    if (DEFAULT_API_BASE_URL) {
      // Only in development builds - this branch is eliminated in production
      return DEFAULT_API_BASE_URL
    }
    // In production, require the env var to be set
    throw new Error(
      'VITE_API_BASE_URL environment variable is required in production. ' +
      'Please set it in your Railway environment variables.'
    )
  }
  const trimmed = rawUrl.replace(/\s+/g, '').replace(/\/+$/, '')
  if (!trimmed) {
    if (DEFAULT_API_BASE_URL) {
      // Only in development builds - this branch is eliminated in production
      return DEFAULT_API_BASE_URL
    }
    throw new Error('VITE_API_BASE_URL cannot be empty in production')
  }
  return trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`
}

export const API_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL)

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: 'application/json',
  },
})
