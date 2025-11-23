import React, { useState, useEffect } from 'react'
import { AxiosError } from 'axios'
import { useAuth } from '../../hooks/useAuth'
import { VCButton } from '../vibecraft'

export interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { login, register, isLoggingIn, isRegistering, loginError, registerError } =
    useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    e.stopPropagation() // Prevent any event bubbling that might cause reload
    setError(null)

    try {
      // Use mutateAsync to properly await the mutation
      if (isLogin) {
        await login({ email, password })
      } else {
        await register({ email, password, display_name: displayName || undefined })
      }
      // Wait a moment for auth state to update and React to re-render
      await new Promise((resolve) => setTimeout(resolve, 300))
      onSuccess()
      onClose()
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string; message?: string }>
      console.error('Auth error:', axiosError)
      console.error('Auth error response:', axiosError?.response)
      console.error('Auth error data:', axiosError?.response?.data)

      // Get the actual error message from various possible locations
      const backendError =
        axiosError?.response?.data?.detail || axiosError?.response?.data?.message

      // Handle specific error cases - only match exact backend error message
      let errorMessage: string
      if (backendError === 'Email already registered') {
        errorMessage = 'Please register with a different email.'
      } else if (backendError) {
        errorMessage = backendError
      } else {
        errorMessage =
          axiosError?.message ||
          String(axiosError) ||
          (isLogin
            ? loginError?.message || 'Login failed. Please try again.'
            : registerError?.message || 'Registration failed. Please try again.')
      }
      setError(errorMessage)
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-md rounded-2xl bg-[rgba(20,20,32,0.95)] backdrop-blur-xl border border-vc-border/50 shadow-2xl p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-vc-text-secondary hover:text-white transition-colors p-2 hover:bg-vc-border/30 rounded-lg"
          aria-label="Close"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        <h1 className="text-3xl font-bold text-white mb-2 text-center">VibeCraft</h1>
        <p className="text-white/70 text-center mb-8">AI Music Video Generator</p>

        <div className="flex gap-4 mb-6">
          <button
            type="button"
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
              isLogin
                ? 'bg-white/20 text-white'
                : 'bg-white/5 text-white/70 hover:bg-white/10'
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
              !isLogin
                ? 'bg-white/20 text-white'
                : 'bg-white/5 text-white/70 hover:bg-white/10'
            }`}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label
                htmlFor="displayName"
                className="block text-white/90 mb-2 text-sm font-medium"
              >
                Display Name (optional)
              </label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
                placeholder="Your name"
              />
            </div>
          )}

          <div>
            <label
              htmlFor="email"
              className="block text-white/90 mb-2 text-sm font-medium"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-white/90 mb-2 text-sm font-medium"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200 text-sm">
              {error}
            </div>
          )}

          <VCButton
            type="submit"
            disabled={isLoggingIn || isRegistering}
            className="w-full"
          >
            {isLogin
              ? isLoggingIn
                ? 'Logging in...'
                : 'Login'
              : isRegistering
                ? 'Registering...'
                : 'Register'}
          </VCButton>
        </form>
      </div>
    </div>
  )
}
