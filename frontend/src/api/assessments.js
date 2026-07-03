import { apiClient, normalisePage } from './client';

export async function listAssessments(params = {}) {
  const response = await apiClient.get('/assessments/', { params });
  return normalisePage(response.data);
}

export async function getAssessment(id) {
  const response = await apiClient.get(`/assessments/${id}/`);
  return response.data;
}
