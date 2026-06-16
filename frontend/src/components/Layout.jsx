import { NavLink } from 'react-router-dom';

const links = [
  ['Analyze', '/analyze'],
  ['Tracker', '/tracker'],
  ['Analytics', '/analytics'],
  ['Evidence Graph', '/evidence']
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
