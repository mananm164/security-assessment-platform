import { apiClient, normalisePage } from './client';

export async function listImports(params = {}) {
  const response = await apiClient.get('/imports/', { params });
  return normalisePage(response.data);
}

export async function listImportObservations(importId) {
  const response = await apiClient.get(`/imports/${importId}/observations/`);
  return normalisePage(response.data);
}
