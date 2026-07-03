import { apiClient, normalisePage } from './client';

export async function listAssets(params = {}) {
  const response = await apiClient.get('/assets/', { params });
  return normalisePage(response.data);
}
