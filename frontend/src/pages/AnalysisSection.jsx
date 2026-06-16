import JsonPanel from '../components/JsonPanel.jsx';

const sectionMap = {
  '/match-report': ['Match Report', 'Skill gap and match scoring from the latest analysis.', 'skill_gap_report'],
  '/resume-suggestions': ['Resume Suggestions', 'Tailored resume bullets and honesty notes from the latest analysis.', 'tailored_resume_bullets'],
  '/linkedin-optimizer': ['LinkedIn Optimizer', 'Headline, About section, skills, and featured project recommendations.', 'linkedin_optimization'],
  '/project-recommendations': ['Project Recommendations', 'Projects recommended to close weak or missing skill gaps.', 'recommended_projects'],
  '/cover-letter': ['Cover Letter', 'Company-specific cover letter generated from evidence-backed claims.', 'cover_letter']
};

function latestAnalysis() {
  const entries = Object.entries(localStorage)
    .filter(([key]) => key.startsWith('analysis:'))
    .map(([key, value]) => ({ key, value }))
    .sort((a, b) => b.key.localeCompare(a.key));
  if (!entries[0]) return null;
  try {
    return JSON.parse(entries[0].value);
  } catch {
    return null;
  }
}

export default function AnalysisSection({ path }) {
  const [title, subtitle, key] = sectionMap[path] || sectionMap['/match-report'];
  const analysis = latestAnalysis();
  const state = analysis?.state || analysis?.output || {};

  return (
    <div>
      <div className="pageHeader">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {!analysis ? (
        <div className="panel">Run an analysis first. This page shows the latest analysis stored in your browser.</div>
      ) : (
        <JsonPanel title={title} data={state[key]} />
      )}
    </div>
  );
}
