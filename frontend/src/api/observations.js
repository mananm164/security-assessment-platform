import { apiClient, normalisePage } from './client';

export async function listObservations(params = {}) {
  const response = await apiClient.get('/observations/', { params });
  return normalisePage(response.data);
}

export async function triageObservation(id, payload) {
  const response = await apiClient.post(`/observations/${id}/triage/`, payload);
  return response.data;
}

export async function promoteObservation(id, payload) {
  const response = await apiClient.post(`/observations/${id}/promote/`, payload);
  return response.data;
}
