import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import Analyze from './pages/Analyze.jsx';
import Approval from './pages/Approval.jsx';
import Tracker from './pages/Tracker.jsx';
import Analytics from './pages/Analytics.jsx';
import EvidenceGraph from './pages/EvidenceGraph.jsx';
import AgentTracing from './pages/AgentTracing.jsx';
import AnalysisSection from './pages/AnalysisSection.jsx';
import ApprovalCenter from './pages/ApprovalCenter.jsx';
import DeploymentStatus from './pages/DeploymentStatus.jsx';
import EvaluationReport from './pages/EvaluationReport.jsx';
import GitHubScanner from './pages/GitHubScanner.jsx';
import ResumeVersioning from './pages/ResumeVersioning.jsx';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Analyze />} />
        <Route path="/upload" element={<Analyze />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/match-report" element={<AnalysisSection path="/match-report" />} />
        <Route path="/resume-suggestions" element={<AnalysisSection path="/resume-suggestions" />} />
        <Route path="/linkedin-optimizer" element={<AnalysisSection path="/linkedin-optimizer" />} />
        <Route path="/github-scanner" element={<GitHubScanner />} />
        <Route path="/project-recommendations" element={<AnalysisSection path="/project-recommendations" />} />
        <Route path="/cover-letter" element={<AnalysisSection path="/cover-letter" />} />
        <Route path="/resume-versioning" element={<ResumeVersioning />} />
        <Route path="/approval/:analysisId" element={<Approval />} />
        <Route path="/approval-center" element={<ApprovalCenter />} />
        <Route path="/tracker" element={<Tracker />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/evidence" element={<EvidenceGraph />} />
        <Route path="/evaluation-report" element={<EvaluationReport />} />
        <Route path="/agent-tracing" element={<AgentTracing />} />
        <Route path="/deployment-status" element={<DeploymentStatus />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  );
}
