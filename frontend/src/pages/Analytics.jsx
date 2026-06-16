import { useEffect, useState } from 'react';
import { getAnalytics } from '../api/client.js';
import JsonPanel from '../components/JsonPanel.jsx';

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getAnalytics()
      .then(setAnalytics)
      .catch((err) => setError(err.response?.data?.detail || err.message || 'Could not load analytics.'));
  }, []);

  if (error) return <div className="panel error">{error}</div>;
  if (!analytics) return <div className="panel">Loading analytics...</div>;

  return (
    <div>
      <div className="pageHeader">
        <h1>Analytics</h1>
        <p>Pipeline and application tracking metrics.</p>
      </div>
      <div className="metricGrid">
        <div className="metric">
          <span>Total Applications</span>
          <strong>{analytics.total_applications}</strong>
        </div>
        <div className="metric">
          <span>Average Match</span>
          <strong>{analytics.average_match_score}%</strong>
        </div>
      </div>
      <JsonPanel title="Status Counts" data={analytics.status_counts} />
      <JsonPanel title="Recent Applications" data={analytics.recent_applications} />
    </div>
  );
}
