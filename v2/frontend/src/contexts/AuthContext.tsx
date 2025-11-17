/** Authentication context for managing user state. */

import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, login, logout as apiLogout, register } from '../api/auth';
import type { User } from '../api/auth';
import { getAuthToken, removeAuthToken } from '../api/client';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Check if user is authenticated on mount
  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      getCurrentUser()
        .then((userData) => {
          setUser(userData);
        })
        .catch(() => {
          // Token is invalid, clear it
          removeAuthToken();
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      // Defer setState to avoid synchronous state update in effect
      setTimeout(() => {
        setLoading(false);
      }, 0);
    }
  }, []);

  const handleLogin = async (email: string, password: string) => {
    const response = await login({ email, password });
    setUser(response.user);
    navigate('/');
  };

  const handleRegister = async (email: string, password: string) => {
    const response = await register({ email, password });
    setUser(response.user);
    navigate('/');
  };

  const handleLogout = () => {
    apiLogout();
    setUser(null);
    navigate('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

