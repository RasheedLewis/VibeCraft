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

  // Initialize token on mount (using useEffect to avoid modifying outside component)
  React.useEffect(() => {
    const token = getToken()
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }, [])

  // Get current user - make token reactive so query enables when token changes
  const [token, setToken] = React.useState<string | null>(() => getToken())

  const {
    data: currentUser,
    isLoading: isLoadingUser,
    refetch: refetchUser,
  } = useQuery<UserInfo>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const response = await apiClient.get<UserInfo>('/auth/me')
      return response.data
    },
    enabled: !!token,
    retry: false,
    staleTime: 0, // Always refetch when enabled
    // If there's no token, we're not loading
    // If query fails, stop loading
    gcTime: 0, // Don't cache failed queries
  })

  // Create setAuth function that has access to refetchUser
  const setAuth = React.useCallback(
    (tokenValue: string, user: UserInfo) => {
      localStorage.setItem(AUTH_TOKEN_KEY, tokenValue)
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
      // Update API client default headers
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokenValue}`
      // Update token state to trigger query
      setToken(tokenValue)
      // Immediately set query data
      queryClient.setQueryData(['auth', 'me'], user)
      // Refetch to verify with backend
      setTimeout(() => {
        refetchUser()
      }, 0)
    },
    [queryClient, refetchUser],
  )

  // Clear auth data
  const clearAuth = React.useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    localStorage.removeItem(AUTH_USER_KEY)
    delete apiClient.defaults.headers.common['Authorization']
    setToken(null)
  }, [])

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
    },
  })

  // Register mutation
  const registerMutation = useMutation<AuthResponse, Error, RegisterRequest>({
    mutationFn: async (credentials) => {
      try {
        const response = await apiClient.post<AuthResponse>('/auth/register', credentials)
        return response.data
      } catch (error) {
        console.error('[useAuth] Register error:', error)
        if (error && typeof error === 'object' && 'response' in error) {
          const axiosError = error as { response?: { data?: unknown } }
          console.error('[useAuth] Error response:', axiosError?.response?.data)
        }
        throw error
      }
    },
    onSuccess: (data) => {
      const user: UserInfo = {
        user_id: data.user_id,
        email: data.email,
        display_name: data.display_name,
      }
      setAuth(data.access_token, user)
    },
  })

  // Logout
  const logout = React.useCallback(() => {
    clearAuth()
    // Clear all query data to reset app state
    queryClient.clear()
    // Invalidate auth query to ensure it refetches as unauthenticated
    queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
  }, [clearAuth, queryClient])

  // Use state token, fallback to getToken() for initial render
  const currentToken = token ?? getToken()
  // Check if authenticated - use currentUser from query OR from localStorage
  const user = currentUser || getUser()
  const isAuthenticated = !!currentToken && !!user

  // Only show loading if we have a token and the query is actually enabled
  // If no token, we're not loading (we know we're not authenticated)
  const isLoading = !!token && isLoadingUser

  return {
    currentUser: user,
    isLoading,
    isAuthenticated,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  }
}
