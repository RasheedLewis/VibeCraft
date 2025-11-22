import React from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'

interface AuthResponse {
  access_token: string
  user_id: string
  email: string
  display_name?: string
}

interface UserInfo {
  user_id: string
  email: string
  display_name?: string
}

interface LoginRequest {
  email: string
  password: string
}

interface RegisterRequest {
  email: string
  password: string
  display_name?: string
}

const AUTH_TOKEN_KEY = 'vibecraft_auth_token'
const AUTH_USER_KEY = 'vibecraft_auth_user'

export function useAuth() {
  const queryClient = useQueryClient()

  // Get token from localStorage
  const getToken = (): string | null => {
    return localStorage.getItem(AUTH_TOKEN_KEY)
  }

  // Get user from localStorage
  const getUser = (): UserInfo | null => {
    const userStr = localStorage.getItem(AUTH_USER_KEY)
    return userStr ? JSON.parse(userStr) : null
  }

  // Set auth data
  const setAuth = (token: string, user: UserInfo) => {
    localStorage.setItem(AUTH_TOKEN_KEY, token)
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
    // Update API client default headers
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  // Clear auth data
  const clearAuth = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    localStorage.removeItem(AUTH_USER_KEY)
    delete apiClient.defaults.headers.common['Authorization']
  }

  // Initialize token on mount (using useEffect to avoid modifying outside component)
  React.useEffect(() => {
    const token = getToken()
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }, [])

  // Get current user
  const { data: currentUser, isLoading: isLoadingUser } = useQuery<UserInfo>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const response = await apiClient.get<UserInfo>('/auth/me')
      return response.data
    },
    enabled: !!token,
    retry: false,
    staleTime: Infinity,
  })

  // Login mutation
  const loginMutation = useMutation<AuthResponse, Error, LoginRequest>({
    mutationFn: async (credentials) => {
      const response = await apiClient.post<AuthResponse>('/auth/login', credentials)
      return response.data
    },
    onSuccess: (data) => {
      const user: UserInfo = {
        user_id: data.user_id,
        email: data.email,
        display_name: data.display_name,
      }
      setAuth(data.access_token, user)
      queryClient.setQueryData(['auth', 'me'], user)
    },
  })

  // Register mutation
  const registerMutation = useMutation<AuthResponse, Error, RegisterRequest>({
    mutationFn: async (credentials) => {
      const response = await apiClient.post<AuthResponse>('/auth/register', credentials)
      return response.data
    },
    onSuccess: (data) => {
      const user: UserInfo = {
        user_id: data.user_id,
        email: data.email,
        display_name: data.display_name,
      }
      setAuth(data.access_token, user)
      queryClient.setQueryData(['auth', 'me'], user)
    },
  })

  // Logout
  const logout = () => {
    clearAuth()
    queryClient.clear()
  }

  return {
    currentUser: currentUser || getUser(),
    isLoading: isLoadingUser,
    isAuthenticated: !!token && !!currentUser,
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  }
}
