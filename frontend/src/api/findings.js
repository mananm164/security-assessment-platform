import { apiClient, normalisePage } from './client';

export async function listFindings(params = {}) {
  const response = await apiClient.get('/findings/', { params });
  return normalisePage(response.data);
}

export async function getFinding(id) {
  const response = await apiClient.get(`/findings/${id}/`);
  return response.data;
}
