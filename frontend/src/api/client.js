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

export async function scanGitHubEvidence(payload) {
  const response = await api.post('/github/scan', payload);
  return response.data;
}

export async function getResumeVersions(userId = 1) {
  const response = await api.get(`/resume-versions/${userId}`);
  return response.data;
}

export async function getResumeVersionDetail(versionId) {
  const response = await api.get(`/resume-versions/detail/${versionId}`);
  return response.data;
}

export async function compareResumeVersions(payload) {
  const response = await api.post('/resume-versions/compare', payload);
  return response.data;
}

export async function exportResumeVersion(payload) {
  const response = await api.post('/resume-versions/export', payload);
  return response.data;
}

export async function getEvaluations(userId = 1) {
  const response = await api.get(`/evaluations/${userId}`);
  return response.data;
}

export async function getEvaluationDetail(evaluationId) {
  const response = await api.get(`/evaluations/detail/${evaluationId}`);
  return response.data;
}

export async function getTraces(userId = 1) {
  const response = await api.get(`/traces/${userId}`);
  return response.data;
}

export async function getTraceRun(graphRunId) {
  const response = await api.get(`/traces/run/${graphRunId}`);
  return response.data;
}

export async function getPendingApprovals(userId = 1) {
  const response = await api.get(`/approval-items/pending/${userId}`);
  return response.data;
}

export async function getApprovalHistory(userId = 1) {
  const response = await api.get(`/approval-items/history/${userId}`);
  return response.data;
}

export async function approveApprovalItem(payload) {
  const response = await api.post('/approval-items/approve', payload);
  return response.data;
}

export async function rejectApprovalItem(payload) {
  const response = await api.post('/approval-items/reject', payload);
  return response.data;
}

export async function regenerateApprovalItem(payload) {
  const response = await api.post('/approval-items/regenerate', payload);
  return response.data;
}

export async function getDeploymentStatus() {
  const response = await api.get('/deployment/status');
  return response.data;
}
