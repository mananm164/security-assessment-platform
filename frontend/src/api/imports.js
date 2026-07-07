import { apiClient, normalisePage } from './client';

export async function listImports(params = {}) {
  const response = await apiClient.get('/imports/', { params });
  return normalisePage(response.data);
}

export async function listImportObservations(importId) {
  const response = await apiClient.get(`/imports/${importId}/observations/`);
  return normalisePage(response.data);
}


export async function createImportPreview(assessmentId, { sourceTool, file }) {
  const formData = new FormData();
  formData.append('source_tool', sourceTool);
  formData.append('report_file', file);
  const response = await apiClient.post(`/assessments/${assessmentId}/import-previews/`, formData);
  return response.data;
}

export async function getImportPreview(previewId) {
  const response = await apiClient.get(`/import-previews/${previewId}/`);
  return response.data;
}

export async function confirmImportPreview(previewId) {
  const response = await apiClient.post(`/import-previews/${previewId}/confirm/`);
  return response.data;
}
