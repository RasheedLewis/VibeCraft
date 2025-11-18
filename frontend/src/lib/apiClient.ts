import axios from 'axios'

// Use Vite's build-time env var to completely exclude localhost from production builds
// import.meta.env.DEV is replaced at build time, and dead code elimination removes the localhost string
// This prevents browsers from detecting localhost references in production bundles
const getDefaultApiBaseUrl = (): string | undefined => {
  // This entire block is eliminated from production builds by Vite's dead code elimination
  if (import.meta.env.DEV) {
    return 'http://localhost:8000/api/v1'
  }
  return undefined
}

const DEFAULT_API_BASE_URL = getDefaultApiBaseUrl()

const normalizeBaseUrl = (rawUrl: string | undefined): string => {
  if (!rawUrl) {
    if (DEFAULT_API_BASE_URL) {
      // Only in development builds - this code is tree-shaken out of production
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
      // Only in development builds - this code is tree-shaken out of production
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
