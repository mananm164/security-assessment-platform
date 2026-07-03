import { apiClient, normalisePage } from './client';

export async function listAuditLogs(params = {}) {
  const response = await apiClient.get('/audit-logs/', { params });
  return normalisePage(response.data);
}
