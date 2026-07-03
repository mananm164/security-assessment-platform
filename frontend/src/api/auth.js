import { apiClient } from './client';

export async function obtainToken(email, password) {
  const response = await apiClient.post('/auth/token/', { email, password });
  return response.data;
}

export async function getCurrentUser() {
  const response = await apiClient.get('/auth/me/');
  return response.data;
}
