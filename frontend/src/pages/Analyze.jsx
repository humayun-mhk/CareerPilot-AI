import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeApplication } from '../api/client.js';
import JsonPanel from '../components/JsonPanel.jsx';

export default function Analyze() {
  const navigate = useNavigate();
  const [resumeFile, setResumeFile] = useState(null);
  const [linkedinFile, setLinkedinFile] = useState(null);
  const [form, setForm] = useState({
    linkedin_text: '',
    job_title: '',
    company_name: '',
    job_link: '',
    job_description: '',
    github_url: '',
    portfolio_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  function updateField(event) {
    setForm({ ...form, [event.target.name]: event.target.value });
  }

  async function submit(event) {
    event.preventDefault();
    setError('');
    if (!resumeFile) {
      setError('Resume PDF is required.');
      return;
    }
    if (!form.job_description.trim()) {
      setError('Job description is required.');
      return;
    }
    if (!linkedinFile && !form.linkedin_text.trim()) {
      setError('Upload a LinkedIn PDF or paste LinkedIn profile text.');
      return;
    }

    const data = new FormData();
    data.append('resume_file', resumeFile);
    if (linkedinFile) data.append('linkedin_file', linkedinFile);
    Object.entries(form).forEach(([key, value]) => data.append(key, value));

    setLoading(true);
    try {
      const response = await analyzeApplication(data);
      setResult(response);
      localStorage.setItem(`analysis:${response.analysis_id}`, JSON.stringify(response));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>Run Analysis</h1>
        <p>Upload the resume, add LinkedIn and job context, then run the LangGraph workflow.</p>
      </div>

      <form className="panel formGrid" onSubmit={submit}>
        <label>
          Resume PDF
          <input type="file" accept="application/pdf" onChange={(event) => setResumeFile(event.target.files[0])} />
        </label>
        <label>
          LinkedIn PDF
          <input type="file" accept="application/pdf" onChange={(event) => setLinkedinFile(event.target.files[0])} />
        </label>
        <label className="span2">
          LinkedIn Text
          <textarea name="linkedin_text" value={form.linkedin_text} onChange={updateField} rows="5" />
        </label>
        <label>
          Job Title
          <input name="job_title" value={form.job_title} onChange={updateField} />
        </label>
        <label>
          Company Name
          <input name="company_name" value={form.company_name} onChange={updateField} />
        </label>
        <label>
          Job Link
          <input name="job_link" value={form.job_link} onChange={updateField} />
        </label>
        <label>
          GitHub URL
          <input name="github_url" value={form.github_url} onChange={updateField} />
        </label>
        <label>
          Portfolio URL
          <input name="portfolio_url" value={form.portfolio_url} onChange={updateField} />
        </label>
        <label className="span2">
          Job Description
          <textarea name="job_description" value={form.job_description} onChange={updateField} rows="8" />
        </label>
        <div className="span2 actionRow">
          <button disabled={loading}>{loading ? 'Running...' : 'Run Multi-Agent Analysis'}</button>
          {error && <span className="error">{error}</span>}
        </div>
      </form>

      {result && (
        <div className="resultsGrid">
          <JsonPanel title="Job Research" data={result.state.job_research} />
          <JsonPanel title="Resume Analysis" data={result.state.resume_analysis} />
          <JsonPanel title="Skill Gap" data={result.state.skill_gap_report} />
          <JsonPanel title="Evidence Report" data={result.state.evidence_report} />
          <button className="wideButton" onClick={() => navigate(`/approval/${result.analysis_id}`)}>
            Review Human Approval
          </button>
        </div>
      )}
    </div>
  );
}
