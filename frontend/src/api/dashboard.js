import { apiClient } from './client';

export async function getDashboardSummary() {
  const response = await apiClient.get('/dashboard/summary/');
  return response.data;
}
