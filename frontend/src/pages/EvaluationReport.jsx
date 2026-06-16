import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { getEvaluationDetail, getEvaluations } from '../api/client.js';
import JsonPanel from '../components/JsonPanel.jsx';

function metricData(report) {
  if (!report) return [];
  return [
    { name: 'Job Match', score: report.job_match_score },
    { name: 'Skill Coverage', score: report.skill_coverage_score },
    { name: 'Evidence', score: report.evidence_confidence_score },
    { name: 'ATS', score: report.ats_keyword_score },
    { name: 'Cover Letter', score: report.cover_letter_personalization_score },
    { name: 'Quality', score: report.overall_quality_score }
  ];
}

export default function EvaluationReport() {
  const [evaluations, setEvaluations] = useState([]);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getEvaluations(1)
      .then((items) => {
        setEvaluations(items);
        if (items[0]) return getEvaluationDetail(items[0].id).then(setDetail);
        return null;
      })
      .catch((err) => setError(err.response?.data?.detail || err.message || 'Could not load evaluations.'));
  }, []);

  async function selectEvaluation(event) {
    const id = event.target.value;
    setDetail(id ? await getEvaluationDetail(id) : null);
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>Evaluation Report</h1>
        <p>Quality, evidence, ATS, hallucination risk, blocked claims, and recommendations.</p>
      </div>
      {error && <div className="panel error">{error}</div>}

      <section className="panel">
        <label>
          Evaluation run
          <select onChange={selectEvaluation} value={detail?.id || ''}>
            <option value="">Select report</option>
            {evaluations.map((item) => (
              <option key={item.id} value={item.id}>
                #{item.id} - Quality {item.overall_quality_score} - {item.created_at}
              </option>
            ))}
          </select>
        </label>
      </section>

      {!detail ? <div className="panel">No evaluation reports yet. Run an analysis first.</div> : (
        <>
          <div className="metricGrid">
            <div className="metric"><span>Overall Quality</span><strong>{detail.overall_quality_score}%</strong></div>
            <div className="metric"><span>Hallucination Risk</span><strong>{detail.hallucination_risk_score}%</strong></div>
            <div className="metric"><span>Evidence Confidence</span><strong>{detail.evidence_confidence_score}%</strong></div>
            <div className="metric"><span>ATS Keywords</span><strong>{detail.ats_keyword_score}%</strong></div>
          </div>
          <section className="panel chartPanel">
            <h2>Metric Breakdown</h2>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={metricData(detail)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="score" fill="#0f766e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </section>
          <div className="resultsGrid">
            <JsonPanel title="Issues Found" data={detail.issues_found} />
            <JsonPanel title="Blocked Claims" data={detail.blocked_claims} />
            <JsonPanel title="Recommendations" data={detail.recommendations} />
            <JsonPanel title="Full Evaluation" data={detail} />
          </div>
        </>
      )}
    </div>
  );
}
