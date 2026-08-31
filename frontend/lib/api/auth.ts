import { apiFetch, setStoredToken, clearStoredToken } from './client';
import { LoginRequest, TokenResponse } from './types';

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await apiFetch<TokenResponse>('/auth/token', {
    method: 'POST',
    body: JSON.stringify({
      username: credentials.username,
      password: credentials.password,
      tenant_id: credentials.tenant_id || 'tenant_default',
    }),
  });

  if (response.access_token) {
    setStoredToken(response.access_token, response.tenant_id);
  }

  return response;
}

export function logout(): void {
  clearStoredToken();
}
