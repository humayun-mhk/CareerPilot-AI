import { useState } from 'react';
import { scanGitHubEvidence } from '../api/client.js';
import JsonPanel from '../components/JsonPanel.jsx';

export default function GitHubScanner() {
  const [githubInput, setGithubInput] = useState('');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    setError('');
    setReport(null);
    if (!githubInput.trim()) {
      setError('Enter a GitHub username or profile URL.');
      return;
    }
    setLoading(true);
    try {
      setReport(await scanGitHubEvidence({ user_id: 1, github_input: githubInput.trim() }));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'GitHub scan failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>GitHub Evidence Scanner</h1>
        <p>Scan public repositories, README files, project types, skills, and evidence confidence.</p>
      </div>

      <form className="panel formGrid" onSubmit={submit}>
        <label className="span2">
          GitHub username or profile URL
          <input value={githubInput} onChange={(event) => setGithubInput(event.target.value)} placeholder="humayun-mhk" />
        </label>
        <div className="span2 actionRow">
          <button disabled={loading}>{loading ? 'Scanning...' : 'Scan GitHub Evidence'}</button>
          {error && <span className="error">{error}</span>}
        </div>
      </form>

      {report && (
        <>
          <div className="metricGrid">
            <div className="metric">
              <span>Repositories Scanned</span>
              <strong>{report.repositories_scanned}</strong>
            </div>
            <div className="metric">
              <span>Detected Skills</span>
              <strong>{Object.keys(report.skill_evidence_summary || {}).length}</strong>
            </div>
          </div>

          <section className="panel">
            <h2>Repository Evidence</h2>
            <div className="cardGrid">
              {(report.projects || []).map((project) => (
                <article className="miniCard" key={project.repo_name}>
                  <div className="rowBetween">
                    <h3>{project.repo_name}</h3>
                    <span className="badge">{Math.round((project.evidence_confidence || 0) * 100)}%</span>
                  </div>
                  <p>{project.project_type}</p>
                  <p>{project.readme_summary}</p>
                  <div className="tagRow">
                    {(project.detected_skills || []).map((skill) => <span className="tag" key={skill}>{skill}</span>)}
                  </div>
                  <a href={project.repo_url} target="_blank" rel="noreferrer">Open repository</a>
                </article>
              ))}
            </div>
          </section>

          <JsonPanel title="Skill Evidence Summary" data={report.skill_evidence_summary} />
          <JsonPanel title="Full GitHub Evidence Report" data={report} />
        </>
      )}
    </div>
  );
}
