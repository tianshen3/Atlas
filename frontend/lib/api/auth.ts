import { apiFetch, setStoredToken, clearStoredToken } from './client';
import { LoginRequest, TokenResponse } from './types';

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await apiFetch<TokenResponse>('/auth/token', {
    method: 'POST',
    body: JSON.stringify({
      email: credentials.email,
      password: credentials.password,
    }),
  });

  if (response.access_token) {
    setStoredToken(response.access_token);
  }

  return response;
}

export function logout(): void {
  clearStoredToken();
}
