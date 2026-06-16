import { NavLink } from 'react-router-dom';

const links = [
  ['Dashboard', '/dashboard'],
  ['Upload Resume', '/upload'],
  ['Job Analyzer', '/analyze'],
  ['Match Report', '/match-report'],
  ['Resume Suggestions', '/resume-suggestions'],
  ['LinkedIn Optimizer', '/linkedin-optimizer'],
  ['GitHub Evidence Scanner', '/github-scanner'],
  ['Project Recommendations', '/project-recommendations'],
  ['Cover Letter', '/cover-letter'],
  ['Resume Versioning', '/resume-versioning'],
  ['Application Tracker', '/tracker'],
  ['Evidence Graph', '/evidence'],
  ['Evaluation Report', '/evaluation-report'],
  ['Agent Tracing', '/agent-tracing'],
  ['Approval Center', '/approval-center'],
  ['Analytics', '/analytics'],
  ['Deployment Status', '/deployment-status']
];

export default function Layout({ children }) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <h1>CareerPilot AI</h1>
        <p>Full-stack multi-agent career assistant</p>
        <nav>
          {links.map(([label, href]) => (
            <NavLink key={href} to={href} className={({ isActive }) => (isActive ? 'active' : '')}>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
