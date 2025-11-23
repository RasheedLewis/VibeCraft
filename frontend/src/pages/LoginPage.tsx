import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { VCButton } from '../components/vibecraft'

export const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login, register, isLoggingIn, isRegistering, loginError, registerError } =
    useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    try {
      if (isLogin) {
        await login({ email, password })
      } else {
        await register({ email, password, display_name: displayName || undefined })
      }
      navigate('/')
    } catch {
      setError(
        isLogin
          ? loginError?.message || 'Login failed. Please try again.'
          : registerError?.message || 'Registration failed. Please try again.',
      )
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="w-full max-w-md p-8 bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl border border-white/20">
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
