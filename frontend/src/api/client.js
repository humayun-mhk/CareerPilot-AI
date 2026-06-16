import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
});

export async function analyzeApplication(formData) {
  const response = await api.post('/analyze', formData);
  return response.data;
}

export async function getAnalysis(analysisId) {
  const response = await api.get(`/analysis/${analysisId}`);
  return response.data;
}

export async function approveAnalysis(analysisId, payload) {
  const response = await api.post(`/approvals/${analysisId}`, payload);
  return response.data;
}

export async function getApplications() {
  const response = await api.get('/applications');
  return response.data;
}

export async function updateApplicationStatus(applicationId, status) {
  const response = await api.patch(`/applications/${applicationId}/status`, { status });
  return response.data;
}

export async function getAnalytics() {
  const response = await api.get('/analytics');
  return response.data;
}

export async function getEvidenceGraph(applicationId = '') {
  const params = applicationId ? { application_id: applicationId } : {};
  const response = await api.get('/evidence-graph', { params });
  return response.data;
}
