import { useEffect, useState } from 'react';
import {
  compareResumeVersions,
  exportResumeVersion,
  getResumeVersionDetail,
  getResumeVersions
} from '../api/client.js';
import JsonPanel from '../components/JsonPanel.jsx';

export default function ResumeVersioning() {
  const [versions, setVersions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [compare, setCompare] = useState({ version_a_id: '', version_b_id: '' });
  const [comparison, setComparison] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function load() {
    try {
      setVersions(await getResumeVersions(1));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not load resume versions.');
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function openDetail(versionId) {
    setSelected(await getResumeVersionDetail(versionId));
  }

  async function exportVersion(versionId, exportFormat) {
    const result = await exportResumeVersion({ user_id: 1, version_id: versionId, export_format: exportFormat });
    setMessage(`Exported ${result.file_name}`);
  }

  async function runCompare(event) {
    event.preventDefault();
    setComparison(await compareResumeVersions({
      version_a_id: Number(compare.version_a_id),
      version_b_id: Number(compare.version_b_id)
    }));
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>Resume Versioning</h1>
        <p>Track tailored resume versions, match score improvements, approvals, and exports.</p>
      </div>
      {error && <div className="panel error">{error}</div>}
      {message && <div className="panel success">{message}</div>}

      <section className="panel">
        <h2>Saved Versions</h2>
        {versions.length === 0 ? <p>No resume versions yet. Run an analysis to generate one.</p> : (
          <table>
            <thead>
              <tr>
                <th>Version</th>
                <th>Company</th>
                <th>Role</th>
                <th>Score Change</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {versions.map((version) => (
                <tr key={version.id}>
                  <td>{version.version_name}</td>
                  <td>{version.company}</td>
                  <td>{version.role}</td>
                  <td>{version.previous_match_score} to {version.improved_match_score}</td>
                  <td><span className="badge">{version.approval_status}</span></td>
                  <td className="actionRow">
                    <button onClick={() => openDetail(version.id)}>View</button>
                    <button className="secondary" onClick={() => exportVersion(version.id, 'pdf')}>PDF</button>
                    <button className="secondary" onClick={() => exportVersion(version.id, 'txt')}>TXT</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <form className="panel formGrid" onSubmit={runCompare}>
        <h2 className="span2">Compare Versions</h2>
        <label>
          First version
          <select value={compare.version_a_id} onChange={(event) => setCompare({ ...compare, version_a_id: event.target.value })}>
            <option value="">Select</option>
            {versions.map((version) => <option value={version.id} key={version.id}>{version.version_name}</option>)}
          </select>
        </label>
        <label>
          Second version
          <select value={compare.version_b_id} onChange={(event) => setCompare({ ...compare, version_b_id: event.target.value })}>
            <option value="">Select</option>
            {versions.map((version) => <option value={version.id} key={version.id}>{version.version_name}</option>)}
          </select>
        </label>
        <button className="span2" disabled={!compare.version_a_id || !compare.version_b_id}>Compare</button>
      </form>

      {selected && <JsonPanel title="Resume Version Detail" data={selected} />}
      {comparison && <JsonPanel title="Version Comparison" data={comparison} />}
    </div>
  );
}
