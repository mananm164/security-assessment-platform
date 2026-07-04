import { apiClient } from './client';

export async function getFindingIntelligence(findingId) {
  const response = await apiClient.get(`/findings/${findingId}/intelligence/`);
  return response.data;
}

export async function refreshFindingIntelligence(findingId, payload = {}) {
  const response = await apiClient.post(`/findings/${findingId}/intelligence/refresh/`, payload);
  return response.data;
}
