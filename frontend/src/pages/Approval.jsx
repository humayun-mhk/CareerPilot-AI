import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { approveAnalysis, getAnalysis } from '../api/client.js';
import JsonPanel from '../components/JsonPanel.jsx';

function bulletsFromState(state) {
  return state?.tailored_resume_bullets?.tailored_bullets || [];
}

function coverLetterFromState(state) {
  return state?.cover_letter?.cover_letter || '';
}

export default function Approval() {
  const { analysisId } = useParams();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState(null);
  const [bullets, setBullets] = useState('');
  const [coverLetter, setCoverLetter] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const cached = localStorage.getItem(`analysis:${analysisId}`);
        const data = cached ? JSON.parse(cached) : await getAnalysis(analysisId);
        const state = data.state || data.output;
        setAnalysis({ ...data, state });
        setBullets(bulletsFromState(state).join('\n'));
        setCoverLetter(coverLetterFromState(state));
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Could not load analysis.');
      }
    }
    load();
  }, [analysisId]);

  async function submit(decision) {
    setError('');
    setMessage('');
    try {
      const payload = {
        decision,
        approved_resume_bullets: bullets
          .split('\n')
          .map((line) => line.replace(/^[-*]\s*/, '').trim())
          .filter(Boolean),
        approved_cover_letter: coverLetter.trim()
      };
      const response = await approveAnalysis(analysisId, payload);
      setMessage(`Approval status: ${response.approval_status}`);
      if (response.application_id) {
        setTimeout(() => navigate('/tracker'), 500);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Approval failed.');
    }
  }

  if (error) return <div className="panel error">{error}</div>;
  if (!analysis) return <div className="panel">Loading analysis...</div>;

  return (
    <div>
      <div className="pageHeader">
        <h1>Human Approval</h1>
        <p>Review sensitive career content before it is saved to SQLite and ChromaDB memory.</p>
      </div>
      <div className="approvalGrid">
        <section className="panel">
          <h2>Resume Bullets</h2>
          <textarea value={bullets} onChange={(event) => setBullets(event.target.value)} rows="12" />
        </section>
        <section className="panel">
          <h2>Cover Letter</h2>
          <textarea value={coverLetter} onChange={(event) => setCoverLetter(event.target.value)} rows="12" />
        </section>
      </div>
      <div className="actionRow">
        <button onClick={() => submit('approved')}>Approve and Save</button>
        <button className="secondary" onClick={() => submit('rejected')}>Reject</button>
        {message && <span className="success">{message}</span>}
      </div>
      <JsonPanel title="Project Recommendations" data={analysis.state.recommended_projects} />
    </div>
  );
}
