/** Authentication API functions. */

import { apiRequest, removeAuthToken, setAuthToken } from './client';

export interface User {
  id: string;
  email: string;
  created_at: string;
  video_count: number;
  storage_bytes: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Register a new user.
 */
export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  setAuthToken(response.access_token);
  return response;
}

/**
 * Login with email and password.
 */
export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  setAuthToken(response.access_token);
  return response;
}

/**
 * Logout the current user.
 */
export function logout(): void {
  removeAuthToken();
}

/**
 * Get the current authenticated user.
 */
export async function getCurrentUser(): Promise<User> {
  return apiRequest<User>('/api/v1/auth/me');
}

