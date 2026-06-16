import { useEffect, useState } from 'react';
import { getApplications, updateApplicationStatus } from '../api/client.js';

const statuses = ['Saved', 'Ready to Apply', 'Applied', 'Follow-up Needed', 'Interview', 'Rejected', 'Offer'];

export default function Tracker() {
  const [applications, setApplications] = useState([]);
  const [error, setError] = useState('');

  async function load() {
    try {
      setApplications(await getApplications());
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not load applications.');
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function changeStatus(id, status) {
    await updateApplicationStatus(id, status);
    await load();
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>Application Tracker</h1>
        <p>Saved applications appear after human approval.</p>
      </div>
      {error && <div className="panel error">{error}</div>}
      <section className="panel">
        <table>
          <thead>
            <tr>
              <th>Company</th>
              <th>Role</th>
              <th>Match</th>
              <th>Status</th>
              <th>Follow-up</th>
            </tr>
          </thead>
          <tbody>
            {applications.map((item) => (
              <tr key={item.id}>
                <td>{item.company_name}</td>
                <td>{item.job_title}</td>
                <td>{item.match_score}%</td>
                <td>
                  <select value={item.status} onChange={(event) => changeStatus(item.id, event.target.value)}>
                    {statuses.map((status) => (
                      <option key={status}>{status}</option>
                    ))}
                  </select>
                </td>
                <td>{item.follow_up_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
