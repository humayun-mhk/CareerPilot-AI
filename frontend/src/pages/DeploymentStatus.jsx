import { useEffect, useState } from 'react';
import { getDeploymentStatus } from '../api/client.js';
import JsonPanel from '../components/JsonPanel.jsx';

export default function DeploymentStatus() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getDeploymentStatus()
      .then(setStatus)
      .catch((err) => setError(err.response?.data?.detail || err.message || 'Could not load deployment status.'));
  }, []);

  return (
    <div>
      <div className="pageHeader">
        <h1>Deployment Status</h1>
        <p>Backend, frontend, database, RAG memory, Docker readiness, and fallback configuration.</p>
      </div>
      {error && <div className="panel error">{error}</div>}
      {!status ? <div className="panel">Loading deployment status...</div> : (
        <>
          <div className="metricGrid">
            <div className="metric"><span>Backend</span><strong>{status.backend}</strong></div>
            <div className="metric"><span>Frontend</span><strong>Vite</strong></div>
            <div className="metric"><span>RAG Memory</span><strong>{status.rag_memory}</strong></div>
            <div className="metric"><span>LLM Fallback</span><strong>{status.llm_fallback ? 'On' : 'Off'}</strong></div>
          </div>
          <JsonPanel title="Deployment Metadata" data={status} />
          <section className="panel">
            <h2>Production Commands</h2>
            <pre>{`Backend: uvicorn backend.main:app --reload --port 8000
Frontend: cd frontend && npm install && npm run dev
Docker: docker compose up --build`}</pre>
          </section>
        </>
      )}
    </div>
  );
}
