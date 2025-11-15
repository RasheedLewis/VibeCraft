import axios from 'axios'

const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1'

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '') ?? DEFAULT_API_BASE_URL

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: 'application/json',
  },
})


