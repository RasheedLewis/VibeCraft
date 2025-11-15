import axios from 'axios'

const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1'

const normalizeBaseUrl = (rawUrl: string | undefined): string => {
  if (!rawUrl) return DEFAULT_API_BASE_URL
  const trimmed = rawUrl.replace(/\s+/g, '').replace(/\/+$/, '')
  if (!trimmed) return DEFAULT_API_BASE_URL
  return trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`
}

export const API_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL)

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: 'application/json',
  },
})


