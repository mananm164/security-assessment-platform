import { apiClient } from './client';

export async function listAIArtifacts(findingId) {
  const response = await apiClient.get(`/findings/${findingId}/ai-artifacts/`);
  return response.data?.items ?? [];
}

export async function generateRemediationDraft(findingId) {
  const response = await apiClient.post(`/findings/${findingId}/ai/remediation/`);
  return response.data;
}
